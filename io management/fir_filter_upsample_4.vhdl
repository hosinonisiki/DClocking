-- ///////////////Documentation////////////////////
-- Contains an fir filter that upsamples input by 4.
-- Width exclusively chosen for this application.

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

architecture butterworth32 of fir_filter_upsample_4 is
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
    -- 32-order butterworth, cutoff at 0.25 * Fs/2

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
    data_0_out <= std_logic_vector(scaled(0)(37 downto 22));
    data_1_out <= std_logic_vector(scaled(1)(37 downto 22));
    data_2_out <= std_logic_vector(scaled(2)(37 downto 22));
    data_3_out <= std_logic_vector(scaled(3)(37 downto 22));
end architecture butterworth32;

architecture equiripple63 of fir_filter_upsample_4 is
    -- [-0.000931293371819803, -0.00109476720252362, -0.000867779622754822, 0.000168964841761851,
    -- 0.00170950953859115, 0.00289428946424997, 0.00272357227112656, 0.000761370841831875,
    -- -0.00231072065257109, -0.00476245936010559, -0.00468309119472664, -0.00128301676838461,
    -- 0.00417660614304565, 0.00861017689718574, 0.00867967056855186, 0.00301337138547026,
    -- -0.00627862123905594, -0.0140268019397481, -0.0146031147309941, -0.00554145446127873,
    -- 0.00994177890686380, 0.0234501728413863, 0.0253769739391643, 0.0107101473168421,
    -- -0.0164370107239297, -0.0425438997814882, -0.0496956880248768, -0.0240884380414676,
    -- 0.0360071999652366, 0.117109278225282, 0.194423623417312, 0.241526826929639,
    -- 0.241526826929639, 0.194423623417312, 0.117109278225282, 0.0360071999652366,
    -- -0.0240884380414676, -0.0496956880248768, -0.0425438997814882, -0.0164370107239297,
    -- 0.0107101473168421, 0.0253769739391643, 0.0234501728413863, 0.00994177890686380,
    -- -0.00554145446127873, -0.0146031147309941, -0.0140268019397481, -0.00627862123905594,
    -- 0.00301337138547026, 0.00867967056855186, 0.00861017689718574, 0.00417660614304565,
    -- -0.00128301676838461, -0.00468309119472664, -0.00476245936010559, -0.00231072065257109,
    -- 0.000761370841831875, 0.00272357227112656, 0.00289428946424997, 0.00170950953859115,
    -- 0.000168964841761851, -0.000867779622754822, -0.00109476720252362, -0.000931293371819803]
    -- 63-order equiripple, pass 103MHz, stop 149MHz, Fs = 1GHz, weight = [1, 5]

    type coef_type is array(0 to 31) of signed(19 downto 0);
    constant coef       :   coef_type := (
        x"FF81A", x"FF6B8", x"FF8A4", x"0016F",
        x"00E7F", x"0188B", x"01718", x"00675",
        x"FEC68", x"FD79E", x"FD84A", x"FF51F",
        x"0236A", x"04902", x"04999", x"0198D",
        x"FCAC3", x"F8910", x"F842D", x"FD103",
        x"0544D", x"0C6D8", x"0D72E", x"05AD1",
        x"F74A0", x"E9741", x"E5A9D", x"F33BF",
        x"13152", x"3E103", x"67097", x"7FFFF"
    ); -- Coefficients mirrored
    constant norm       :   signed(19 downto 0) := x"7BA97";
    
    type product_buf_type is array(0 to 31) of signed(35 downto 0);
    signal product_buf  :   product_buf_type := (others => (others => '0'));

    type product_type_m is array(0 to 31) of signed(23 downto 0);
    signal product_0    :   product_type_m := (others => (others => '0'));
    signal product_1    :   product_type_m := (others => (others => '0'));
    signal product_2    :   product_type_m := (others => (others => '0'));
    signal product_3    :   product_type_m := (others => (others => '0'));
    signal product_4    :   product_type_m := (others => (others => '0'));
    signal product_5    :   product_type_m := (others => (others => '0'));
    signal product_6    :   product_type_m := (others => (others => '0'));
    signal product_7    :   product_type_m := (others => (others => '0'));
    signal product_8    :   product_type_m := (others => (others => '0'));
    signal product_9    :   product_type_m := (others => (others => '0'));
    signal product_10   :   product_type_m := (others => (others => '0'));
    signal product_11   :   product_type_m := (others => (others => '0'));
    signal product_12   :   product_type_m := (others => (others => '0'));
    signal product_13   :   product_type_m := (others => (others => '0'));
    signal product_14   :   product_type_m := (others => (others => '0'));
    signal product_15   :   product_type_m := (others => (others => '0'));

    type product_type is array(0 to 63) of signed(23 downto 0);
    signal product      :   product_type := (others => (others => '0'));

    type sum_0_type is array(0 to 15) of signed(23 downto 0);
    signal sum_0        :   sum_0_type := (others => (others => '0'));

    type sum_1_type is array(0 to 3) of signed(23 downto 0);
    signal sum_1        :   sum_1_type := (others => (others => '0'));

    type scaled_type is array(0 to 3) of signed(43 downto 0);
    signal scaled       :   scaled_type := (others => (others => '0'));
begin
    gen_product_buf : for i in 0 to 31 generate
        product_buf(i) <= signed(data_in) * coef(i);
    end generate;

    gen_product_0 : for i in 0 to 31 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    product_0(i) <= (others => '0');
                else
                    product_0(i) <= (3 downto 0 => product_buf(i)(35)) & product_buf(i)(35 downto 16);
                end if;
            end if;
        end process;
    end generate;
    
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                product_1 <= (others => (others => '0'));
                product_2 <= (others => (others => '0'));
                product_3 <= (others => (others => '0'));
                product_4 <= (others => (others => '0'));
                product_5 <= (others => (others => '0'));
                product_6 <= (others => (others => '0'));
                product_7 <= (others => (others => '0'));
                product_8 <= (others => (others => '0'));
                product_9 <= (others => (others => '0'));
                product_10 <= (others => (others => '0'));
                product_11 <= (others => (others => '0'));
                product_12 <= (others => (others => '0'));
                product_13 <= (others => (others => '0'));
                product_14 <= (others => (others => '0'));
                product_15 <= (others => (others => '0'));
            else
                product_1 <= product_0;
                product_2 <= product_1;
                product_3 <= product_2;
                product_4 <= product_3;
                product_5 <= product_4;
                product_6 <= product_5;
                product_7 <= product_6;
                product_8 <= product_7;
                product_9 <= product_8;
                product_10 <= product_9;
                product_11 <= product_10;
                product_12 <= product_11;
                product_13 <= product_12;
                product_14 <= product_13;
                product_15 <= product_14;
            end if;
        end if;
    end process;

    product(0) <= product_0(0);
    product(1) <= product_0(1);
    product(2) <= product_0(2);
    product(3) <= product_0(3);
    product(4) <= product_1(4);
    product(5) <= product_1(5);
    product(6) <= product_1(6);
    product(7) <= product_1(7);
    product(8) <= product_2(8);
    product(9) <= product_2(9);
    product(10) <= product_2(10);
    product(11) <= product_2(11);
    product(12) <= product_3(12);
    product(13) <= product_3(13);
    product(14) <= product_3(14);
    product(15) <= product_3(15);
    product(16) <= product_4(16);
    product(17) <= product_4(17);
    product(18) <= product_4(18);
    product(19) <= product_4(19);
    product(20) <= product_5(20);
    product(21) <= product_5(21);
    product(22) <= product_5(22);
    product(23) <= product_5(23);
    product(24) <= product_6(24);
    product(25) <= product_6(25);
    product(26) <= product_6(26);
    product(27) <= product_6(27);
    product(28) <= product_7(28);
    product(29) <= product_7(29);
    product(30) <= product_7(30);
    product(31) <= product_7(31);
    product(32) <= product_8(31);
    product(33) <= product_8(30);
    product(34) <= product_8(29);
    product(35) <= product_8(28);
    product(36) <= product_9(27);
    product(37) <= product_9(26);
    product(38) <= product_9(25);
    product(39) <= product_9(24);
    product(40) <= product_10(23);
    product(41) <= product_10(22);
    product(42) <= product_10(21);
    product(43) <= product_10(20);
    product(44) <= product_11(19);
    product(45) <= product_11(18);
    product(46) <= product_11(17);
    product(47) <= product_11(16);
    product(48) <= product_12(15);
    product(49) <= product_12(14);
    product(50) <= product_12(13);
    product(51) <= product_12(12);
    product(52) <= product_13(11);
    product(53) <= product_13(10);
    product(54) <= product_13(9);
    product(55) <= product_13(8);
    product(56) <= product_14(7);
    product(57) <= product_14(6);
    product(58) <= product_14(5);
    product(59) <= product_14(4);
    product(60) <= product_15(3);
    product(61) <= product_15(2);
    product(62) <= product_15(1);
    product(63) <= product_15(0);

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
                sum_0(8) <= product(32) + product(36) + product(40) + product(44);
                sum_0(9) <= product(33) + product(37) + product(41) + product(45);
                sum_0(10) <= product(34) + product(38) + product(42) + product(46);
                sum_0(11) <= product(35) + product(39) + product(43) + product(47);
                sum_0(12) <= product(48) + product(52) + product(56) + product(60);
                sum_0(13) <= product(49) + product(53) + product(57) + product(61);
                sum_0(14) <= product(50) + product(54) + product(58) + product(62);
                sum_0(15) <= product(51) + product(55) + product(59) + product(63);
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
                sum_1(0) <= sum_0(0) + sum_0(4) + sum_0(8) + sum_0(12);
                sum_1(1) <= sum_0(1) + sum_0(5) + sum_0(9) + sum_0(13);
                sum_1(2) <= sum_0(2) + sum_0(6) + sum_0(10) + sum_0(14);
                sum_1(3) <= sum_0(3) + sum_0(7) + sum_0(11) + sum_0(15);
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
    data_0_out <= std_logic_vector(scaled(0)(37 downto 22));
    data_1_out <= std_logic_vector(scaled(1)(37 downto 22));
    data_2_out <= std_logic_vector(scaled(2)(37 downto 22));
    data_3_out <= std_logic_vector(scaled(3)(37 downto 22));
end architecture equiripple63;