-- ///////////////Documentation////////////////////
-- Simple FIR filter that uses 24bit coefficient
-- accuracy and supports exactly 64 taps.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity fir_filter is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(4095 downto 0);
        -- data flow ports
        sig_in          :   in  std_logic_vector(15 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity fir_filter;

architecture behavioural of fir_filter is
    signal sig_in_buf   :   signed(15 downto 0) := (others => '0');
    signal sig_out_buf  :   signed(15 downto 0) := (others => '0');

    type coef_type is array (0 to 63) of signed(23 downto 0); -- Normalized to Q1.23, -1 to 1
    signal coef         :   coef_type := (others => (others => '0'));
    signal norm_64      :   signed(17 downto 0); -- Q5.13, -16 to 16
    signal norm_32      :   signed(17 downto 0); -- Q6.12, -32 to 32
    signal norm_16      :   signed(17 downto 0); -- Q7.11, -64 to 64
    -- less taps requires larger scaling factor to keep the same L1 norm of impulse response
    signal taps         :   unsigned(5 downto 0);

    type data_type is array(0 to 63) of signed(15 downto 0); -- Treat as Q1.15, -1 to 1
    signal data         :   data_type := (others => (others => '0'));

    type product_buf_type is array(0 to 63) of signed(39 downto 0); -- Q2.38, -2 to 2 but expected range is -1 to 1
    signal product_buf  :   product_buf_type := (others => (others => '0'));

    type product_type is array(0 to 63) of signed(26 downto 0); -- Q6.21, -32 to 32 but expected range is -1 to 1
    signal product      :   product_type := (others => (others => '0'));

    -- When coef normed to 1, L1 norm of impulse response typicallt won't exceed 64 / 2 = 32, so Q6.21 is sufficient. Use 27 bits to keep accuracy.
    type sum_0_type is array(0 to 15) of signed(26 downto 0); -- Q6.21
    signal sum_0        :   sum_0_type := (others => (others => '0'));

    type sum_1_type is array(0 to 3) of signed(26 downto 0); -- Q6.21
    signal sum_1        :   sum_1_type := (others => (others => '0'));

    signal sum_1_5      :   signed(26 downto 0); -- Q6.21

    signal sum_2        :   signed(26 downto 0); -- Q6.21, -32 to 32, but can be within -2 to 2 most of the time. Even smaller for taps less than 64.

    signal scaled_64    :   signed(44 downto 0); -- Q11.34, -1024 to 1,024 but expected range is -32 to 32 (Use norm_64 to scale the L1 norm of impulse response to 32)
    signal scaled_32    :   signed(44 downto 0); -- Q12.33, -2048 to 2,048 but expected range is -32 to 32 (use norm_32 to scale the L1 norm of impulse response to 32)
    signal scaled_16    :   signed(44 downto 0); -- Q13.32, -4096 to 4,096 but expected range is -32 to 32 (use norm_16 to scale the L1 norm of impulse response to 32)
    -- Truncate to Q6.10, 16bit output, -32 to 32 but treated as -1 to 1
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_in_buf <= (others => '0');
                else
                    sig_in_buf <= signed(sig_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => '0') when rst = '1' else signed(sig_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_out <= (others => '0');
                else
                    sig_out <= std_logic_vector(sig_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => '0') when rst = '1' else std_logic_vector(sig_out_buf);
    end generate;

    gen_coef : for i in 0 to 63 generate
        coef(i) <= signed(core_param_in(i * 32 + 23 downto i * 32)); -- address 0x00 to 0x3F
    end generate;
    norm_64 <= signed(core_param_in(2065 downto 2048)); -- address 0x40
    norm_32 <= signed(core_param_in(2097 downto 2080)); -- address 0x41
    norm_16 <= signed(core_param_in(2129 downto 2112)); -- address 0x42
    taps <= unsigned(core_param_in(2149 downto 2144)); -- address 0x43

    gen_data : for i in 1 to 63 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    data(i) <= (others => '0');
                else
                    data(i) <= data(i-1);
                end if;
            end if;
        end process;
    end generate;
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                data(0) <= (others => '0');
            else
                data(0) <= sig_in_buf;
            end if;
        end if;
    end process;

    gen_product : for i in 0 to 63 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    product(i) <= (others => '0');
                else
                    product(i) <= (3 downto 0 => product_buf(i)(39)) & product_buf(i)(39 downto 17);
                end if;
            end if;
        end process;
    end generate;

    gen_product_buf : for i in 0 to 63 generate
        product_buf(i) <= data(i) * coef(i);
    end generate;

    -- First stage of summation tree
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sum_0 <= (others => (others => '0'));
            else
                sum_0(0) <= product(0) + product(1) + product(2) + product(3);
                sum_0(1) <= product(4) + product(5) + product(6) + product(7);
                sum_0(2) <= product(8) + product(9) + product(10) + product(11);
                sum_0(3) <= product(12) + product(13) + product(14) + product(15);
                sum_0(4) <= product(16) + product(17) + product(18) + product(19);
                sum_0(5) <= product(20) + product(21) + product(22) + product(23);
                sum_0(6) <= product(24) + product(25) + product(26) + product(27);
                sum_0(7) <= product(28) + product(29) + product(30) + product(31);
                sum_0(8) <= product(32) + product(33) + product(34) + product(35);
                sum_0(9) <= product(36) + product(37) + product(38) + product(39);
                sum_0(10) <= product(40) + product(41) + product(42) + product(43);
                sum_0(11) <= product(44) + product(45) + product(46) + product(47);
                sum_0(12) <= product(48) + product(49) + product(50) + product(51);
                sum_0(13) <= product(52) + product(53) + product(54) + product(55);
                sum_0(14) <= product(56) + product(57) + product(58) + product(59);
                sum_0(15) <= product(60) + product(61) + product(62) + product(63);
            end if;
        end if;
    end process;

    -- Second stage of summation tree
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sum_1 <= (others => (others => '0'));
            else
                sum_1(0) <= sum_0(0) + sum_0(1) + sum_0(2) + sum_0(3);
                sum_1(1) <= sum_0(4) + sum_0(5) + sum_0(6) + sum_0(7);
                sum_1(2) <= sum_0(8) + sum_0(9) + sum_0(10) + sum_0(11);
                sum_1(3) <= sum_0(12) + sum_0(13) + sum_0(14) + sum_0(15);
            end if;
        end if;
    end process;

    -- Third stage of summation tree
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sum_2 <= (others => '0'); -- Q6.21
                sum_1_5 <= (others => '0');
            else
                sum_2 <= sum_1(0) + sum_1(1) + sum_1(2) + sum_1(3);
                sum_1_5 <= sum_1(0) + sum_1(1);
            end if;
        end if;
    end process;

    -- Scaling
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                scaled_64 <= (others => '0'); -- Q11.34, Truncate to Q6.10 for output
                scaled_32 <= (others => '0'); -- Q12.33, Truncate to Q6.10 for output
                scaled_16 <= (others => '0'); -- Q13.32, Truncate to Q6.10 for output
            else
                scaled_64 <= sum_2 * norm_64;
                scaled_32 <= sum_1_5 * norm_32;
                scaled_16 <= sum_1(0) * norm_16;
            end if;
        end if;
    end process;

    -- sig_out_buf <= scaled_64(39 downto 24);
    sig_out_buf <= scaled_16(37 downto 22) when taps <= "001111" else
                   scaled_32(38 downto 23) when taps <= "011111" else
                   scaled_64(39 downto 24);

end architecture behavioural;






