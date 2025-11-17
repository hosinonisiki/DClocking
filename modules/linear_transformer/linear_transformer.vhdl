-- ///////////////Documentation////////////////////
-- Performs linear transformation for 2 input signals.
-- Coefficients limited between -1 and 1. Magnification
-- should be done outside the module.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity linear_transformer is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(127 downto 0);
        -- data flow ports
        sig_a_in        :   in  std_logic_vector(15 downto 0);
        sig_b_in        :   in  std_logic_vector(15 downto 0);
        sig_a_out       :   out std_logic_vector(15 downto 0);
        sig_b_out       :   out std_logic_vector(15 downto 0)
    );
end entity linear_transformer;

architecture behavioural of linear_transformer is
    signal sig_a_in_buf     :   signed(15 downto 0); -- Q16.0
    signal sig_b_in_buf     :   signed(15 downto 0);
    signal sig_a_out_buf    :   signed(15 downto 0);
    signal sig_b_out_buf    :   signed(15 downto 0);

    signal coef_aa          :   signed(15 downto 0); -- Q1.15
    signal coef_ab          :   signed(15 downto 0);
    signal coef_ba          :   signed(15 downto 0);
    signal coef_bb          :   signed(15 downto 0);

    signal product_aa       :   signed(31 downto 0); -- Q17.15
    signal product_ab       :   signed(31 downto 0);
    signal product_ba       :   signed(31 downto 0);
    signal product_bb       :   signed(31 downto 0);

    signal sum_a            :   signed(32 downto 0); -- Q18.15
    signal sum_b            :   signed(32 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_a_in_buf <= (others => '0');
                    sig_b_in_buf <= (others => '0');
                else
                    sig_a_in_buf <= signed(sig_a_in);
                    sig_b_in_buf <= signed(sig_b_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_a_in_buf <= (others => '0') when rst = '1' else signed(sig_a_in);
        sig_b_in_buf <= (others => '0') when rst = '1' else signed(sig_b_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_a_out <= (others => '0');
                    sig_b_out <= (others => '0');
                else
                    sig_a_out <= std_logic_vector(sig_a_out_buf);
                    sig_b_out <= std_logic_vector(sig_b_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_a_out <= (others => '0') when rst = '1' else std_logic_vector(sig_a_out_buf);
        sig_b_out <= (others => '0') when rst = '1' else std_logic_vector(sig_b_out_buf);
    end generate;

    coef_aa <= signed(core_param_in(15 downto 0)); -- address 0x00
    coef_ab <= signed(core_param_in(47 downto 32)); -- address 0x01
    coef_ba <= signed(core_param_in(79 downto 64)); -- address 0x02
    coef_bb <= signed(core_param_in(111 downto 96)); -- address 0x03

    process(clk)
    begin
        if rising_edge(clk) then
            product_aa <= coef_aa * sig_a_in_buf;
            product_ab <= coef_ab * sig_b_in_buf;
            product_ba <= coef_ba * sig_a_in_buf;
            product_bb <= coef_bb * sig_b_in_buf;
        end if;
    end process;

    sum_a <= (product_aa(31) & product_aa) + (product_ab(31) & product_ab);
    sum_b <= (product_ba(31) & product_ba) + (product_bb(31) & product_bb);

    sig_a_out_buf <= x"7FFF" when sum_a(32) = '0' and (sum_a(31) = '1' or sum_a(30) = '1') else
                        x"8000" when sum_a(32) = '1' and (sum_a(31) = '0' or sum_a(30) = '0') else
                        sum_a(30 downto 15);
    sig_b_out_buf <= x"7FFF" when sum_b(32) = '0' and (sum_b(31) = '1' or sum_b(30) = '1') else
                        x"8000" when sum_b(32) = '1' and (sum_b(31) = '0' or sum_b(30) = '0') else
                        sum_b(30 downto 15);
end architecture behavioural;






