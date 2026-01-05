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
        error_in     :   in  std_logic_vector(15 downto 0);
        -- control ports
        pause_in        :   in  std_logic;
        auto_reset_in   :   in  std_logic
    );
end entity accumulator;

architecture behavioral of accumulator is
    signal delta        :   unsigned(63 downto 0);
    signal total_incre  :   unsigned(63 downto 0);

    signal divisor      :   std_logic_vector(15 downto 0); -- the divisor N
    signal divisor_digit    :   integer; -- log of the divisor

    -- The phase of acc_out is the first 16 bits of acc.
    -- To make fast_out N times faster, use the logN ~ 15+logN th bits of acc as its phase.
    -- The feedback is aligned with fast phase in order to get better precision while preserving range.
    -- This allows the fast_out to be adjusted between 0 and 0.5 sampling frequency, resulting in the dynamic range of acc_out N times smaller of that.
    signal error_in_buf  :   std_logic_vector(15 downto 0); -- allows the increment to be adjusted
    signal error_shifted :   std_logic_vector(63 downto 0);

    -- Internal loop filter
    -- When lf is enabled, error is considered to be signed.
    -- When bypassed, error is directly added to the accumulator and thus considered unsigned.
    signal bypass_lf    :   std_logic;
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
                else
                    error_in_buf <= error_in;
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        error_in_buf <= (others => '0') when internal_rst = '1' else error_in;
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
    bypass_lf <= core_param_in(192); -- Address 0x06
    enable_auto_reset <= core_param_in(224); -- Address 0x07

    divisor_digit <= 15 when divisor(15) = '1' else
                     14 when divisor(14) = '1' else
                     13 when divisor(13) = '1' else
                     12 when divisor(12) = '1' else
                     11 when divisor(11) = '1' else
                     10 when divisor(10) = '1' else
                     9 when divisor(9) = '1' else
                     8 when divisor(8) = '1' else
                     7 when divisor(7) = '1' else
                     6 when divisor(6) = '1' else
                     5 when divisor(5) = '1' else
                     4 when divisor(4) = '1' else
                     3 when divisor(3) = '1' else
                     2 when divisor(2) = '1' else
                     1 when divisor(1) = '1' else
                     0; -- either divisor is x"0001" or x"0000"

    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                acc <= (others => '0');
            else
                if pause_in = '0' then
                    acc <= acc + total_incre;
                end if;
                if bypass_lf = '1' then
                    total_incre <= unsigned(error_shifted) + delta;
                else
                    total_incre <= unsigned(lf_sum_shifted) + delta;
                end if;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                lf_integral <= (others => '0');
            else
                lf_integral <= lf_integral_limited + (lf_product_i(47) & lf_product_i);
            end if;
            lf_product_p <= lf_kp * signed(error_in_buf);
            lf_product_i <= lf_ki * signed(error_in_buf);
            lf_sum <= (lf_product_p(39) & lf_product_p & x"00") + lf_integral_limited;
        end if;
    end process;
    lf_integral_limited <= "0_01111111_11111111_11111111_11111111_11111111_11111111" when lf_integral(48 downto 47) = "01" else
                           "1_10000000_00000000_00000000_00000000_00000000_00000000" when lf_integral(48 downto 47) = "10" else
                           lf_integral;
    error_shifted <= error_in_buf & (47 downto 0 => '0') when divisor_digit = 0 else
                        (divisor_digit - 1 downto 0 => error_in_buf(15)) & error_in_buf & (47 - divisor_digit downto 0 => '0');
    lf_sum_shifted <= lf_sum & (14 downto 0 => '0') when divisor_digit = 0 else
                        (14 downto 0 => lf_sum(48)) & lf_sum when divisor_digit = 15 else
                        (divisor_digit - 1 downto 0 => lf_sum(48)) & lf_sum & (14 - divisor_digit downto 0 => '0');

    acc_out_buf <= acc(63 downto 48);
    fast_out_buf <= acc(63 - divisor_digit downto 48 - divisor_digit);
end architecture behavioral;