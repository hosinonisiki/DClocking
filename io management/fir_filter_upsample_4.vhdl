-- ///////////////Documentation////////////////////
-- Contains an fir filter that upsamples input by 4.
-- Width exclusively chosen for this application.

-- Deprecated:
-- [-4.69296871e-07 -3.19629908e-06  7.50874994e-06  5.53205609e-05
-- -5.63156245e-05 -4.57651913e-04  2.62806248e-04  2.42386013e-03
-- -8.54120305e-04 -9.34917480e-03  2.04988873e-03  2.87954584e-02
-- -3.75812934e-03 -7.99873844e-02  5.36875620e-03  3.08522768e-01
--  4.93960149e-01  3.08522768e-01  5.36875620e-03 -7.99873844e-02
-- -3.75812934e-03  2.87954584e-02  2.04988873e-03 -9.34917480e-03
-- -8.54120305e-04  2.42386013e-03  2.62806248e-04 -4.57651913e-04
-- -5.63156245e-05  5.53205609e-05  7.50874994e-06 -3.19629908e-06
-- -4.69296871e-07]

-- Correct:
-- [-5.07243765e-08 -9.29737176e-07 -7.51720626e-06 -3.36479230e-05
-- -7.85192201e-05 -3.39767447e-06  6.36694623e-04  2.25937459e-03
--  3.69206643e-03  5.54385078e-04 -1.18347349e-02 -2.82117492e-02
-- -2.49327163e-02  2.82487953e-02  1.34451333e-01  2.47187170e-01
--  2.96146890e-01  2.47187170e-01  1.34451333e-01  2.82487953e-02
-- -2.49327163e-02 -2.82117492e-02 -1.18347349e-02  5.54385078e-04
--  3.69206643e-03  2.25937459e-03  6.36694623e-04 -3.39767447e-06
-- -7.85192201e-05 -3.36479230e-05 -7.51720626e-06 -9.29737176e-07
-- -5.07243765e-08]
-- 32-order linear phase, cutoff at 0.25 * Fs/2

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity fir_filter_upsample_4 is
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;
        data_in     :   in  std_logic_vector(15 downto 0);
        data_0_out  :   out std_logic_vector(15 downto 0);
        data_1_out  :   out std_logic_vector(15 downto 0);
        data_2_out  :   out std_logic_vector(15 downto 0);
        data_3_out  :   out std_logic_vector(15 downto 0)
    );
end entity fir_filter_upsample_4;

architecture behavioural of fir_filter_upsample_4 is
    type coef_type is array(0 to 31) of signed(19 downto 0);
    constant coef       :   coef_type := (
        x"FFFFE", x"FFFF3", x"FFFC4", x"FFF75",
        x"FFFFA", x"00467", x"00FA0", x"01988",
        x"003D5", x"FAE28", x"F3CE7", x"F5394",
        x"0C35B", x"3A1CB", x"6AD6B", x"7FFFF",
        x"6AD6B", x"3A1CB", x"0C35B", x"F5394",
        x"F3CE7", x"FAE28", x"003D5", x"01988",
        x"00FA0", x"00467", x"FFFFA", x"FFF75",
        x"FFFC4", x"FFFF3", x"FFFFE", x"00000"
    );
    constant norm       :   signed(19 downto 0) := x"4A04D";

    type data_type is array(0 to 31) of signed(15 downto 0);
    signal data         :   data_type := (others => (others => '0'));
    
    type product_buf_type is array(0 to 31) of signed(35 downto 0);
    signal product_buf  :   product_buf_type := (others => (others => '0'));

    type product_type is array(0 to 31) of signed(23 downto 0);
    signal product      :   product_type := (others => (others => '0'));

    type sum_0_type is array(0 to 7) of signed(23 downto 0);
    signal sum_0        :   sum_0_type := (others => (others => '0'));

    type sum_1_type is array(0 to 3) of signed(23 downto 0);
    signal sum_1        :   sum_1_type := (others => (others => '0'));

    type scaled_type is array(0 to 3) of signed(43 downto 0);
    signal scaled       :   scaled_type := (others => (others => '0'));
begin
    gen_data_0_to_3 : for i in 0 to 3 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    data(i) <= (others => '0');
                else
                    data(i) <= signed(data_in);
                end if;
            end if;
        end process;
    end generate;

    gen_data_4_to_31 : for i in 4 to 31 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    data(i) <= (others => '0');
                else
                    data(i) <= data(i - 4);
                end if;
            end if;
        end process;
    end generate;

    gen_product : for i in 0 to 31 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    product(i) <= (others => '0');
                else
                    product(i) <= (3 downto 0 => product_buf(i)(35)) & product_buf(i)(35 downto 16);
                end if;
            end if;
        end process;
    end generate;

    gen_product_buf : for i in 0 to 31 generate
        product_buf(i) <= data(i) * coef(i); -- Q4.20
    end generate;

    -- First stage of summation tree
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                sum_0 <= (others => (others => '0'));
            else
                sum_0(0) <= product(0) + product(4) + product(8) + product(12);
                sum_0(1) <= product(1) + product(5) + product(9) + product(13);
                sum_0(2) <= product(2) + product(6) + product(10) + product(14);
                sum_0(3) <= product(3) + product(7) + product(11) + product(15);
                sum_0(4) <= product(16) + product(20) + product(24) + product(28);
                sum_0(5) <= product(17) + product(21) + product(25) + product(29);
                sum_0(6) <= product(18) + product(22) + product(26) + product(30);
                sum_0(7) <= product(19) + product(23) + product(27) + product(31);
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
                sum_1(0) <= sum_0(0) + sum_0(4);
                sum_1(1) <= sum_0(1) + sum_0(5);
                sum_1(2) <= sum_0(2) + sum_0(6);
                sum_1(3) <= sum_0(3) + sum_0(7);
            end if;
        end if;
    end process;

    -- Scaling
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                scaled <= (others => (others => '0'));
            else
                scaled(0) <= norm * sum_1(0); -- Q0.20 * Q4.20 = Q4.40
                scaled(1) <= norm * sum_1(1);
                scaled(2) <= norm * sum_1(2);
                scaled(3) <= norm * sum_1(3);
            end if;
        end if;
    end process;

    -- Upsampling by 4 causes the output to be 4 times smaller, so shift left by extra 2 bits here.
    data_0_out <= std_logic_vector(scaled(0)(36 downto 21));
    data_1_out <= std_logic_vector(scaled(1)(36 downto 21));
    data_2_out <= std_logic_vector(scaled(2)(36 downto 21));
    data_3_out <= std_logic_vector(scaled(3)(36 downto 21));
end architecture behavioural;