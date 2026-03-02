-- ///////////////Documentation////////////////////
-- Simple accumulator providing stimulus for testing
-- purposes.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity accumulator is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(255 downto 0);

        -- data flow ports
        acc_out         :   out std_logic_vector(15 downto 0);
        fast_out        :   out std_logic_vector(15 downto 0); -- provide an aux output N times the freqeuency of acc_out
        error_in     :   in  std_logic_vector(15 downto 0); -- for lf feedback
        bias_in      :   in  std_logic_vector(15 downto 0); -- bias to be added directly
        -- control ports
        pause_in        :   in  std_logic;
        lf_reset_in     :   in  std_logic;
        auto_reset_in   :   in  std_logic
    );
end entity accumulator;

architecture behavioral of accumulator is
    signal delta        :   unsigned(63 downto 0);
    signal total_incre  :   unsigned(63 downto 0);
    signal total_feedback   :   unsigned(63 downto 0);

    signal divisor      :   std_logic_vector(15 downto 0) := (others => '0'); -- the divisor N
    signal divisor_digit    :   unsigned(3 downto 0); -- log of the divisor

    type bias_shifted_buf_type is array (0 to 15) of std_logic_vector(63 downto 0);
    signal bias_shifted_buf :   bias_shifted_buf_type;
    type lf_sum_shifted_buf_type is array (0 to 15) of signed(63 downto 0);
    signal lf_sum_shifted_buf  :   lf_sum_shifted_buf_type;

    -- The phase of acc_out is the first 16 bits of acc.
    -- To make fast_out N times faster, use the logN ~ 15+logN th bits of acc as its phase.
    -- The feedback is aligned with fast phase in order to get better precision while preserving range.
    -- This allows the fast_out to be adjusted between 0 and 0.5 sampling frequency, resulting in the dynamic range of acc_out N times smaller of that.
    signal error_in_buf  :   std_logic_vector(15 downto 0); -- allows the increment to be adjusted
    signal bias_in_buf   :   std_logic_vector(15 downto 0);
    signal bias_shifted  :   std_logic_vector(63 downto 0);

    -- Internal loop filter
    signal lf_kp        :   signed(23 downto 0);
    signal lf_ki        :   signed(31 downto 0);
    signal lf_product_p :   signed(39 downto 0);
    signal lf_product_i :   signed(47 downto 0);
    signal lf_integral  :   signed(48 downto 0);
    signal lf_integral_limited  :   signed(48 downto 0);
    signal lf_sum       :   signed(48 downto 0);
    signal lf_sum_shifted       :   signed(63 downto 0);

    signal acc_out_buf  :   unsigned(15 downto 0);
    signal fast_out_buf :   unsigned(15 downto 0);
    signal acc          :   unsigned(63 downto 0);

    signal internal_rst         :   std_logic;
    signal enable_auto_reset    :   std_logic;
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    error_in_buf <= (others => '0');
                    bias_in_buf <= (others => '0');
                else
                    error_in_buf <= error_in;
                    bias_in_buf <= bias_in;
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        error_in_buf <= (others => '0') when internal_rst = '1' else error_in;
        bias_in_buf <= (others => '0') when internal_rst = '1' else bias_in;
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    acc_out <= (others => '0');
                    fast_out <= (others => '0');
                else
                    acc_out <= std_logic_vector(acc_out_buf);
                    fast_out <= std_logic_vector(fast_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        acc_out <= (others => '0') when internal_rst = '1' else std_logic_vector(acc_out_buf);
        fast_out <= (others => '0') when internal_rst = '1' else std_logic_vector(fast_out_buf);
    end generate;

    internal_rst <= '1' when rst = '1' or (enable_auto_reset = '1' and auto_reset_in = '1') else '0';

    delta <= unsigned(core_param_in(63 downto 0)); -- Address 0x00 ~ 0x01
    divisor <= core_param_in(79 downto 64); -- Address 0x02, power of 2 only
    lf_kp <= signed(core_param_in(151 downto 128)); -- Address 0x04
    lf_ki <= signed(core_param_in(191 downto 160)); -- Address 0x05
    enable_auto_reset <= core_param_in(224); -- Address 0x07

    divisor_digit <= x"f" when divisor(15) = '1' else
                     x"e" when divisor(14) = '1' else
                     x"d" when divisor(13) = '1' else
                     x"c" when divisor(12) = '1' else
                     x"b" when divisor(11) = '1' else
                     x"a" when divisor(10) = '1' else
                     x"9" when divisor(9) = '1' else
                     x"8" when divisor(8) = '1' else
                     x"7" when divisor(7) = '1' else
                     x"6" when divisor(6) = '1' else
                     x"5" when divisor(5) = '1' else
                     x"4" when divisor(4) = '1' else
                     x"3" when divisor(3) = '1' else
                     x"2" when divisor(2) = '1' else
                     x"1" when divisor(1) = '1' else
                     x"0"; -- either divisor is x"0001" or x"0000"
    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                acc <= (others => '0');
            else
                if pause_in = '0' then
                    acc <= acc + total_incre;
                end if;
                total_feedback <= unsigned(bias_shifted) + unsigned(lf_sum_shifted);
                total_incre <= delta + total_feedback;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' or lf_reset_in = '1' then
                lf_integral <= (others => '0');
                lf_sum <= (others => '0');
            else
                lf_integral <= lf_integral_limited + (lf_product_i(47) & lf_product_i);
                lf_sum <= (lf_product_p(39) & lf_product_p & x"00") + lf_integral_limited;
            end if;
            lf_product_p <= lf_kp * signed(error_in_buf);
            lf_product_i <= lf_ki * signed(error_in_buf);
        end if;
    end process;
    lf_integral_limited <= b"0_01111111_11111111_11111111_11111111_11111111_11111111" when lf_integral(48 downto 47) = "01" else
                           b"1_10000000_00000000_00000000_00000000_00000000_00000000" when lf_integral(48 downto 47) = "10" else
                           lf_integral;

    bias_shifted_buf(0) <= bias_in_buf & (47 downto 0 => '0');
    lf_sum_shifted_buf(0) <= lf_sum & (14 downto 0 => '0');
    gen_shifted_buf : for i in 1 to 14 generate
        bias_shifted_buf(i) <= (i - 1 downto 0 => bias_in_buf(15)) & bias_in_buf & (47 - i downto 0 => '0');
        lf_sum_shifted_buf(i) <= (i - 1 downto 0 => lf_sum(48)) & lf_sum & (14 - i downto 0 => '0');
    end generate;
    bias_shifted_buf(15) <= (14 downto 0 => bias_in_buf(15)) & bias_in_buf & (32 downto 0 => '0');
    lf_sum_shifted_buf(15) <= (14 downto 0 => lf_sum(48)) & lf_sum;
    bias_shifted <= bias_shifted_buf(to_integer(divisor_digit));
    lf_sum_shifted <= lf_sum_shifted_buf(to_integer(divisor_digit));

    acc_out_buf <= acc(63 downto 48);
    fast_out_buf <= acc(63 - to_integer(divisor_digit) downto 48 - to_integer(divisor_digit));
end architecture behavioral;