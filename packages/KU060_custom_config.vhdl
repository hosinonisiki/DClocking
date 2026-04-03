library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package KU060_custom_config is
    type init_lut_type is array(natural range <>) of std_logic_vector(67 downto 0);
    constant init_lut_size : natural := ; -- Blank for now, max 255
    constant init_lut : init_lut_type(0 to init_lut_size - 1) := (
        -- trx_ss_out(3 downto 0) | trx_control_out(31 downto 0) | trx_dout(31 downto 0)

    );

    type query_lut_type is array(natural range <>) of std_logic_vector(131 downto 0);
    constant query_lut_size : natural := ; -- Blank for now, max 4, same as the width of query_result_out
    constant query_lut : query_lut_type(0 to query_lut_size - 1) := (
        -- trx_ss_out(3 downto 0) | trx_control_out(31 downto 0) | trx_dout(31 downto 0) | query_result_mask(31 downto 0) | expected_query_result(31 downto 0)

    );
end package KU060_custom_config;