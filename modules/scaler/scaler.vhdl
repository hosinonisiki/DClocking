-- ///////////////Documentation////////////////////
-- Linearly scales & adds bias to an input signal.
-- No clamp is applied to the output.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity scaler is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(63 downto 0);
        sig_in          :   in  std_logic_vector(15 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity scaler;

architecture behavioral of scaler is
    signal sig_in_buf   :   signed(15 downto 0);
    signal sig_out_buf  :   signed(15 downto 0);

    signal scale        :   signed(31 downto 0);
    signal bias         :   signed(15 downto 0);
    signal product      :   signed(47 downto 0);
    signal product_1    :   signed(47 downto 0);
begin
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

    scale <= signed(core_param_in(31 downto 0));
    bias <= signed(core_param_in(47 downto 32));
    product <= sig_in_buf * scale;
    sig_out_buf <= product_1(31 downto 16) + bias;

    process(clk)
    begin
        if rising_edge(clk) then
            product_1 <= product;
        end if;
    end process;
end architecture behavioral;