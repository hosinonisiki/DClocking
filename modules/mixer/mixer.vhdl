-- ///////////////Documentation////////////////////
-- Multiplies 2 signals. Truncations are made so that
-- overflow will never happen. If needed, scale the 
-- inputs up before feeding into this module.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity mixer is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        -- data flow ports
        sig_a_in        :   in  std_logic_vector(15 downto 0);
        sig_b_in        :   in  std_logic_vector(15 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity mixer;

architecture behavioural of mixer is
    signal sig_a_buf   :   signed(15 downto 0);
    signal sig_b_buf   :   signed(15 downto 0);
    signal sig_out_buf :   signed(15 downto 0);

    signal product     :   signed(31 downto 0); -- Full precision product
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_a_buf <= (others => '0');
                    sig_b_buf <= (others => '0');
                else
                    sig_a_buf <= signed(sig_a_in);
                    sig_b_buf <= signed(sig_b_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_a_buf <= (others => '0') when rst = '1' else signed(sig_a_in);
        sig_b_buf <= (others => '0') when rst = '1' else signed(sig_b_in);
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

    product <= sig_a_buf * sig_b_buf; -- Use io_buf if this line causes timing issues
    sig_out_buf <= product(31 downto 16);
end architecture behavioural;






