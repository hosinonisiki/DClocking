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
        core_param_in   :   in  std_logic_vector(63 downto 0);
        acc_out         :   out std_logic_vector(15 downto 0)
    );
end entity accumulator;

architecture behavioral of accumulator is
    signal acc_out_buf  :   unsigned(15 downto 0);
    signal acc          :   unsigned(63 downto 0);
begin
    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    acc_out <= (others => '0');
                else
                    acc_out <= std_logic_vector(acc_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        acc_out <= (others => '0') when rst = '1' else std_logic_vector(acc_out_buf);
    end generate;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                acc <= (others => '0');
            else
                acc <= acc + unsigned(core_param_in);
            end if;
        end if;
    end process;
    acc_out_buf <= acc(63 downto 48);
end architecture behavioral;