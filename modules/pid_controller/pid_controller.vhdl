-- ///////////////Documentation////////////////////
-- Simple PID controller. Optimized for speed.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity pid_controller is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(255 downto 0);
        -- data flow ports
        error_in        :   in  std_logic_vector(15 downto 0);
        feedback_out    :   out std_logic_vector(15 downto 0);
        -- control ports
        auto_reset_in   :   in  std_logic
    );
end entity pid_controller;

architecture behavioural of pid_controller is
    signal error_in_buf    :   signed(15 downto 0);
    signal feedback_out_buf :   signed(15 downto 0);

    -- Each "x" "_" "z" and "y" represents 4 bits, with the "x" aligned with final output,
    -- "y" representing dont care, "z" representing bits to be discarded and "_" representing unused bits.
    signal error_from_setpoint   :   signed(15 downto 0);
    signal error_1      :   signed(15 downto 0);
    signal differential :   signed(15 downto 0);
    signal integral     :   signed(47 downto 0); -- yy xxxx yzzz zz__

    signal gain_p       :   signed(23 downto 0); -- When gain_p equals gain_i, PI corner at clk / 2pi / 65536 = 600Hz for 250MHz clock
    signal gain_i       :   signed(31 downto 0);
    signal gain_d       :   signed(23 downto 0);
    
    signal product_p    :   signed(39 downto 0); -- yy xxxx yzzz ____
    signal product_i    :   signed(47 downto 0); -- __ xxxx yyyy yyzz
    signal product_d    :   signed(39 downto 0); -- yy xxxx yzzz ____

    signal setpoint         :   signed(15 downto 0);
    signal limit_integral   :   signed(47 downto 0); -- yy xxxx yyyy yy__ pad with zeros
    signal limit_sum        :   signed(27 downto 0); -- yy xxxx y___ ____ pad with zeros
    signal leak_digit       :   std_logic_vector(31 downto 0); -- Not enough resource to implement a division for leaky integral, so use this signal to represent the digits to be shifted

    signal integral_buf         :   signed(47 downto 0); -- yy xxxx yyyy yy__
    signal integral_buf_limited :   signed(47 downto 0); -- yy xxxx yyyy yy__
    signal sum                  :   signed(27 downto 0); -- yy xxxx y___ ____
    signal sum_buf              :   signed(27 downto 0); -- yy xxxx y___ ____
    signal sum_buf_limited      :   signed(27 downto 0); -- yy xxxx y___ ____
    type leak_array_type is array(0 to 31) of std_logic_vector(47 downto 0);
    signal leak_array           :   leak_array_type; -- Calculate the leak for any given leak_digit, AND them with each bit of leak_digit
    signal integral_leak        :   std_logic_vector(47 downto 0); -- yy xxxx yyyy yy__, OR of leak_array

    signal interleaving_clk     :   std_logic := '0';

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
                    error_in_buf <= signed(error_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        error_in_buf <= (others => '0') when internal_rst = '1' else signed(error_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    feedback_out <= (others => '0');
                else
                    feedback_out <= std_logic_vector(feedback_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        feedback_out <= (others => '0') when internal_rst = '1' else std_logic_vector(feedback_out_buf);
    end generate;

    internal_rst <= '1' when rst = '1' or (enable_auto_reset = '1' and auto_reset_in = '1') else '0';

    gain_p <= signed(core_param_in(23 downto 0)); -- address 0x00
    gain_i <= signed(core_param_in(63 downto 32)); -- address 0x01
    gain_d <= signed(core_param_in(87 downto 64)); -- address 0x02
    setpoint <= signed(core_param_in(111 downto 96)); -- address 0x03
    limit_integral <= x"00" & signed(core_param_in(143 downto 128)) & x"000000"; -- address 0x04
    limit_sum <= x"00" & signed(core_param_in(175 downto 160)) & x"0"; -- address 0x05
    leak_digit <= core_param_in(223 downto 192); -- address 0x06
    enable_auto_reset <= core_param_in(224); -- address 0x07

    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                integral <= (others => '0');
            else
                integral <= integral_buf_limited;
            end if;
            error_from_setpoint <= error_in_buf - setpoint;
            error_1 <= error_in_buf;
            differential <= error_in_buf - error_1;
            product_p <= gain_p * error_from_setpoint;
            product_i <= gain_i * error_from_setpoint;
            product_d <= gain_d * differential;
            sum <= sum_buf;
            feedback_out_buf <= sum_buf_limited(19 downto 4);
            interleaving_clk <= not interleaving_clk;
        end if;
    end process;

    -- Add 1 layer of pipelining, omit half of input data to avoid inconsistency.
    -- This is equivalent to lowering the sampling frequency by half for the integral calculation.
    process(clk)
    begin
        if rising_edge(clk) then
            if interleaving_clk = '1' then
                integral_buf <= integral + ((7 downto 0 => product_i(47)) & product_i(47 downto 8)) + ((46 downto 0 => '0') & product_i(7)) - signed(integral_leak);
            end if;
        end if;
    end process;
    integral_buf_limited <= limit_integral when integral_buf > limit_integral else
                            -limit_integral when integral_buf < -limit_integral else
                            integral_buf;

    sum_buf <= product_p(39 downto 12) + integral(47 downto 20) + product_d(39 downto 12);
    sum_buf_limited <= limit_sum when sum > limit_sum else
                    -limit_sum when sum < -limit_sum else
                    sum;

    array_gen : for i in 0 to 31 generate
        leak_array(i) <= (7 + i downto 0 => integral(47)) & std_logic_vector(integral(47 downto i + 8)) when leak_digit(i) = '1' else (others => '0');
    end generate;
    leak_gen : for i in 47 downto 0 generate
        integral_leak(i) <= leak_array(0)(i) or leak_array(1)(i) or leak_array(2)(i) or leak_array(3)(i) or
                           leak_array(4)(i) or leak_array(5)(i) or leak_array(6)(i) or leak_array(7)(i) or
                           leak_array(8)(i) or leak_array(9)(i) or leak_array(10)(i) or leak_array(11)(i) or
                           leak_array(12)(i) or leak_array(13)(i) or leak_array(14)(i) or leak_array(15)(i) or
                           leak_array(16)(i) or leak_array(17)(i) or leak_array(18)(i) or leak_array(19)(i) or
                           leak_array(20)(i) or leak_array(21)(i) or leak_array(22)(i) or leak_array(23)(i) or
                           leak_array(24)(i) or leak_array(25)(i) or leak_array(26)(i) or leak_array(27)(i) or
                           leak_array(28)(i) or leak_array(29)(i) or leak_array(30)(i) or leak_array(31)(i);
    end generate;
end architecture behavioural;






