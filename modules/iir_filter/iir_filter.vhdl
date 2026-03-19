-- ///////////////Documentation////////////////////
-- 4th order IIR employing the parallel biquad structure
-- with 4th order scattered look-ahead. The bit widths
-- have been carefully chosen and tested to reach balance
-- between precision, stability and resource usage for
-- all common IIR type and all possible cutoff frequency.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity iir_filter is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(1023 downto 0);
        -- data flow ports
        sig_in         :   in  std_logic_vector(15 downto 0);
        sig_out        :   out std_logic_vector(15 downto 0)
    );
end entity iir_filter;

architecture behavioural of iir_filter is
    signal sig_in_buf   : signed(15 downto 0) := (others => '0');
    signal sig_out_buf  : signed(15 downto 0) := (others => '0');

    -- bq stands for biquad, b and a correspond to the ba coeffcients
    -- Each biquad is 4th order scattered, so it takes 9 b and 2 a coefficients
    -- Q3.24
    signal bq1_b_0      : signed(26 downto 0) := (others => '0');
    signal bq1_b_1      : signed(26 downto 0) := (others => '0');
    signal bq1_b_2      : signed(26 downto 0) := (others => '0');
    signal bq1_b_3      : signed(26 downto 0) := (others => '0');
    signal bq1_b_4      : signed(26 downto 0) := (others => '0');
    signal bq1_b_5      : signed(26 downto 0) := (others => '0');
    signal bq1_b_6      : signed(26 downto 0) := (others => '0');
    signal bq1_b_7      : signed(26 downto 0) := (others => '0');
    signal bq1_b_8      : signed(26 downto 0) := (others => '0');
    signal bq2_b_0      : signed(26 downto 0) := (others => '0');
    signal bq2_b_1      : signed(26 downto 0) := (others => '0');
    signal bq2_b_2      : signed(26 downto 0) := (others => '0');
    signal bq2_b_3      : signed(26 downto 0) := (others => '0');
    signal bq2_b_4      : signed(26 downto 0) := (others => '0');
    signal bq2_b_5      : signed(26 downto 0) := (others => '0');
    signal bq2_b_6      : signed(26 downto 0) := (others => '0');
    signal bq2_b_7      : signed(26 downto 0) := (others => '0');
    signal bq2_b_8      : signed(26 downto 0) := (others => '0');
    -- Q2.25
    signal bq1_a_4      : signed(26 downto 0) := (others => '0');
    signal bq1_a_8      : signed(26 downto 0) := (others => '0');
    signal bq2_a_4      : signed(26 downto 0) := (others => '0');
    signal bq2_a_8      : signed(26 downto 0) := (others => '0');

    -- Products, Q3.24 * Q1.15 = Q4.39, reduced to Q4.26
    signal bq1_xb_0_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_1_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_2_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_3_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_4_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_5_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_6_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_7_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_8_buf     : signed(42 downto 0) := (others => '0');
    signal bq1_xb_0         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_1         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_2         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_3         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_4         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_5         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_6         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_7         : signed(29 downto 0) := (others => '0');
    signal bq1_xb_8         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_0_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_1_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_2_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_3_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_4_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_5_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_6_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_7_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_8_buf     : signed(42 downto 0) := (others => '0');
    signal bq2_xb_0         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_1         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_2         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_3         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_4         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_5         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_6         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_7         : signed(29 downto 0) := (others => '0');
    signal bq2_xb_8         : signed(29 downto 0) := (others => '0');

    -- For y, Q2.25 * Q4.26 = Q6.51, reduced to Q4.26
    signal bq1_ya_4_buf     : signed(56 downto 0) := (others => '0');
    signal bq1_ya_8_buf     : signed(56 downto 0) := (others => '0');
    signal bq1_ya_4         : signed(29 downto 0) := (others => '0');
    signal bq1_ya_8         : signed(29 downto 0) := (others => '0');
    signal bq2_ya_4_buf     : signed(56 downto 0) := (others => '0');
    signal bq2_ya_8_buf     : signed(56 downto 0) := (others => '0');
    signal bq2_ya_4         : signed(29 downto 0) := (others => '0');
    signal bq2_ya_8         : signed(29 downto 0) := (others => '0');

    -- Long multiplication for y requires breaking it down into smaller parts
    -- Here Q4.26 is broken down into a higher 18 bits and a lower 12 bits
    -- Pad one '0' before the lower part
    signal bq1_ya_4_high    : signed(44 downto 0) := (others => '0');
    signal bq1_ya_4_low     : signed(39 downto 0) := (others => '0');
    signal bq1_ya_8_high    : signed(44 downto 0) := (others => '0');
    signal bq1_ya_8_low     : signed(39 downto 0) := (others => '0');
    signal bq2_ya_4_high    : signed(44 downto 0) := (others => '0');
    signal bq2_ya_4_low     : signed(39 downto 0) := (others => '0');
    signal bq2_ya_8_high    : signed(44 downto 0) := (others => '0');
    signal bq2_ya_8_low     : signed(39 downto 0) := (others => '0');

    -- Partial sums
    signal bq1_sum_xb_0     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_1     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_2     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_3     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_4     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_5     : signed(29 downto 0) := (others => '0');    
    signal bq1_sum_xb_6     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_7     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_xb_8     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_0     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_1     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_2     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_3     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_4     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_5     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_6     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_7     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_xb_8     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_ya_0     : signed(29 downto 0) := (others => '0');
    signal bq1_sum_ya_1     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_ya_0     : signed(29 downto 0) := (others => '0');
    signal bq2_sum_ya_1     : signed(29 downto 0) := (others => '0');

    -- Stages
    signal bq1_ya_8_0       : signed(29 downto 0) := (others => '0');
    signal bq1_ya_8_1       : signed(29 downto 0) := (others => '0');
    signal bq1_ya_8_2       : signed(29 downto 0) := (others => '0');
    signal bq1_ya_8_3       : signed(29 downto 0) := (others => '0');
    signal bq2_ya_8_0       : signed(29 downto 0) := (others => '0');
    signal bq2_ya_8_1       : signed(29 downto 0) := (others => '0');
    signal bq2_ya_8_2       : signed(29 downto 0) := (others => '0');
    signal bq2_ya_8_3       : signed(29 downto 0) := (others => '0');

    signal result           : signed(29 downto 0);

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

    bq1_b_0 <= signed(core_param_in(26 downto 0));
    bq1_b_1 <= signed(core_param_in(58 downto 32));
    bq1_b_2 <= signed(core_param_in(90 downto 64));
    bq1_b_3 <= signed(core_param_in(122 downto 96));
    bq1_b_4 <= signed(core_param_in(154 downto 128));
    bq1_b_5 <= signed(core_param_in(186 downto 160));
    bq1_b_6 <= signed(core_param_in(218 downto 192));
    bq1_b_7 <= signed(core_param_in(250 downto 224));
    bq1_b_8 <= signed(core_param_in(282 downto 256));
    bq1_a_4 <= signed(core_param_in(314 downto 288));
    bq1_a_8 <= signed(core_param_in(346 downto 320));
    bq2_b_0 <= signed(core_param_in(378 downto 352));
    bq2_b_1 <= signed(core_param_in(410 downto 384));
    bq2_b_2 <= signed(core_param_in(442 downto 416));
    bq2_b_3 <= signed(core_param_in(474 downto 448));
    bq2_b_4 <= signed(core_param_in(506 downto 480));
    bq2_b_5 <= signed(core_param_in(538 downto 512));
    bq2_b_6 <= signed(core_param_in(570 downto 544));
    bq2_b_7 <= signed(core_param_in(602 downto 576));
    bq2_b_8 <= signed(core_param_in(634 downto 608));
    bq2_a_4 <= signed(core_param_in(666 downto 640));
    bq2_a_8 <= signed(core_param_in(698 downto 672));

    -- Biquad 1
    process(clk)
    begin
        if rising_edge(clk) then
            bq1_xb_0 <= bq1_xb_0_buf(42 downto 13);
            bq1_xb_1 <= bq1_xb_1_buf(42 downto 13);
            bq1_xb_2 <= bq1_xb_2_buf(42 downto 13);
            bq1_xb_3 <= bq1_xb_3_buf(42 downto 13);
            bq1_xb_4 <= bq1_xb_4_buf(42 downto 13);
            bq1_xb_5 <= bq1_xb_5_buf(42 downto 13);
            bq1_xb_6 <= bq1_xb_6_buf(42 downto 13);
            bq1_xb_7 <= bq1_xb_7_buf(42 downto 13);
            bq1_xb_8 <= bq1_xb_8_buf(42 downto 13);

            bq1_ya_4 <= bq1_ya_4_buf(54 downto 25);
            bq1_ya_8 <= bq1_ya_8_buf(54 downto 25);

            bq1_sum_xb_1 <= bq1_sum_xb_2 + bq1_xb_1;
            bq1_sum_xb_2 <= bq1_sum_xb_3 + bq1_xb_2;
            bq1_sum_xb_3 <= bq1_sum_xb_4 + bq1_xb_3;
            bq1_sum_xb_4 <= bq1_sum_xb_5 + bq1_xb_4;
            bq1_sum_xb_5 <= bq1_sum_xb_6 + bq1_xb_5;
            bq1_sum_xb_6 <= bq1_sum_xb_7 + bq1_xb_6;
            bq1_sum_xb_7 <= bq1_sum_xb_8 + bq1_xb_7;
            bq1_sum_xb_8 <= bq1_xb_8;

            bq1_sum_ya_0 <= bq1_sum_ya_1 + bq1_sum_xb_0;
            bq1_sum_ya_1 <= bq1_ya_8_3 + bq1_ya_4;
            bq1_ya_8_3 <= bq1_ya_8_2;
            bq1_ya_8_2 <= bq1_ya_8_1;
            bq1_ya_8_1 <= bq1_ya_8_0;
            bq1_ya_8_0 <= bq1_ya_8;
            bq1_ya_4_high <= bq1_a_4 * bq1_sum_ya_0(29 downto 12);
            bq1_ya_4_low <= bq1_a_4 * ('0' & bq1_sum_ya_0(11 downto 0));
            bq1_ya_8_high <= bq1_a_8 * bq1_sum_ya_0(29 downto 12);
            bq1_ya_8_low <= bq1_a_8 * ('0' & bq1_sum_ya_0(11 downto 0));
            
        end if;
    end process;
    bq1_xb_0_buf <= bq1_b_0 * sig_in_buf;
    bq1_xb_1_buf <= bq1_b_1 * sig_in_buf;
    bq1_xb_2_buf <= bq1_b_2 * sig_in_buf;
    bq1_xb_3_buf <= bq1_b_3 * sig_in_buf;
    bq1_xb_4_buf <= bq1_b_4 * sig_in_buf;
    bq1_xb_5_buf <= bq1_b_5 * sig_in_buf;
    bq1_xb_6_buf <= bq1_b_6 * sig_in_buf;
    bq1_xb_7_buf <= bq1_b_7 * sig_in_buf;
    bq1_xb_8_buf <= bq1_b_8 * sig_in_buf;
    bq1_sum_xb_0 <= bq1_sum_xb_1 + bq1_xb_0;
    bq1_ya_4_buf <= (bq1_ya_4_high & (11 downto 0 => '0')) + ((16 downto 0 => bq1_ya_4_low(39)) & bq1_ya_4_low);
    bq1_ya_8_buf <= (bq1_ya_8_high & (11 downto 0 => '0')) + ((16 downto 0 => bq1_ya_8_low(39)) & bq1_ya_8_low);

    -- Biquad 2
    process(clk)
    begin
        if rising_edge(clk) then
            bq2_xb_0 <= bq2_xb_0_buf(42 downto 13);
            bq2_xb_1 <= bq2_xb_1_buf(42 downto 13);
            bq2_xb_2 <= bq2_xb_2_buf(42 downto 13);
            bq2_xb_3 <= bq2_xb_3_buf(42 downto 13);
            bq2_xb_4 <= bq2_xb_4_buf(42 downto 13);
            bq2_xb_5 <= bq2_xb_5_buf(42 downto 13);
            bq2_xb_6 <= bq2_xb_6_buf(42 downto 13);
            bq2_xb_7 <= bq2_xb_7_buf(42 downto 13);
            bq2_xb_8 <= bq2_xb_8_buf(42 downto 13);

            bq2_ya_4 <= bq2_ya_4_buf(54 downto 25);
            bq2_ya_8 <= bq2_ya_8_buf(54 downto 25);

            bq2_sum_xb_1 <= bq2_sum_xb_2 + bq2_xb_1;
            bq2_sum_xb_2 <= bq2_sum_xb_3 + bq2_xb_2;
            bq2_sum_xb_3 <= bq2_sum_xb_4 + bq2_xb_3;
            bq2_sum_xb_4 <= bq2_sum_xb_5 + bq2_xb_4;
            bq2_sum_xb_5 <= bq2_sum_xb_6 + bq2_xb_5;
            bq2_sum_xb_6 <= bq2_sum_xb_7 + bq2_xb_6;
            bq2_sum_xb_7 <= bq2_sum_xb_8 + bq2_xb_7;
            bq2_sum_xb_8 <= bq2_xb_8;

            bq2_sum_ya_0 <= bq2_sum_ya_1 + bq2_sum_xb_0;
            bq2_sum_ya_1 <= bq2_ya_8_3 + bq2_ya_4;
            bq2_ya_8_3 <= bq2_ya_8_2;
            bq2_ya_8_2 <= bq2_ya_8_1;
            bq2_ya_8_1 <= bq2_ya_8_0;
            bq2_ya_8_0 <= bq2_ya_8;
            bq2_ya_4_high <= bq2_a_4 * bq2_sum_ya_0(29 downto 12);
            bq2_ya_4_low <= bq2_a_4 * ('0' & bq2_sum_ya_0(11 downto 0));
            bq2_ya_8_high <= bq2_a_8 * bq2_sum_ya_0(29 downto 12);
            bq2_ya_8_low <= bq2_a_8 * ('0' & bq2_sum_ya_0(11 downto 0));
            
        end if;
    end process;
    bq2_xb_0_buf <= bq2_b_0 * sig_in_buf;
    bq2_xb_1_buf <= bq2_b_1 * sig_in_buf;
    bq2_xb_2_buf <= bq2_b_2 * sig_in_buf;
    bq2_xb_3_buf <= bq2_b_3 * sig_in_buf;
    bq2_xb_4_buf <= bq2_b_4 * sig_in_buf;
    bq2_xb_5_buf <= bq2_b_5 * sig_in_buf;
    bq2_xb_6_buf <= bq2_b_6 * sig_in_buf;
    bq2_xb_7_buf <= bq2_b_7 * sig_in_buf;
    bq2_xb_8_buf <= bq2_b_8 * sig_in_buf;
    bq2_sum_xb_0 <= bq2_sum_xb_1 + bq2_xb_0;
    bq2_ya_4_buf <= (bq2_ya_4_high & (11 downto 0 => '0')) + ((16 downto 0 => bq2_ya_4_low(39)) & bq2_ya_4_low);
    bq2_ya_8_buf <= (bq2_ya_8_high & (11 downto 0 => '0')) + ((16 downto 0 => bq2_ya_8_low(39)) & bq2_ya_8_low);

    result <= bq1_sum_ya_0 + bq2_sum_ya_0;
    sig_out_buf <= x"7FFF" when result(29) = '0' and (result(28) = '1' or result(27) = '1' or result(26) = '1') else
                    x"8000" when result(29) = '1' and (result(28) = '0' or result(27) = '0' or result(26) = '0') else
                    result(26 downto 11);
end architecture behavioural;






