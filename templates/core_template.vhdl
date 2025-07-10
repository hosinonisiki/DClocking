-- ///////////////Documentation////////////////////
-- The file describes the structure of the core entity
-- of a module. It includes general templates for io
-- buffer generation and auto reset control.

-- Substitute <module_name> with the actual module
-- name, <size> with the size of the parameter ram,
-- in accordance with the module template.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity <module_name> is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(<size> - 1 downto 0);
        -- data flow ports

        -- control ports
        auto_reset_in   :   in  std_logic
    );
end entity <module_name>;

architecture behavioural of <module_name> is
    signal internal_rst         :   std_logic;
    signal enable_auto_reset    :   std_logic;
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then

                else

                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate

    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then

                else

                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate

    end generate;

    internal_rst <= '1' when rst = '1' or (enable_auto_reset = '1' and auto_reset_in = '1') else '0';
end architecture behavioural;






