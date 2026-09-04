library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package KU060_custom_config is
    type init_lut_type is array(natural range <>) of std_logic_vector(67 downto 0);
    -- LMK initialization remains owned by the MicroBlaze.
    constant init_lut_size : natural := 0;
    constant init_lut : init_lut_type(0 to 0) := (
        0 => (others => '0')
    );

    type query_lut_type is array(natural range <>) of std_logic_vector(131 downto 0);
    constant query_lut_size : natural := 1;
    constant query_lut : query_lut_type(0 to query_lut_size - 1) := (
        -- trx_ss_out | trx_control_out | trx_dout | mask | expected
        -- LMK04828 R0x182[1] = PLL1 digital lock detect.
        0 => x"0_0000_0F17_8182_0000_0000_0002_0000_0002"
    );
end package KU060_custom_config;
