-- ///////////////Documentation////////////////////
-- Package for global defined constants.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mypak is
    constant module_count : integer := 1; -- Number of modules connected to the bus.

    type buf_type is (buf_for_io, buf_i_only, buf_o_only, buf_none); -- Universal io buffer type for the core modules.

    constant dbus_w     :   integer := 32; -- Width of the data bus.
    constant abus_w     :   integer := 5; -- Width of the address bus. This determines the size of individual memories in each module.
    constant mbus_w     :   integer := 5; -- Width of the module selection bus. This determines the max number of modules that can be connected to the bus.
    constant cbus_w     :   integer := 5; -- Width of the control bus.
    constant rbus_w     :   integer := 32; -- Width of the response bus.
    constant sbus_w     :   integer := 3; -- Width of the response status bus.
    constant core_param_size : integer := 2 ** abus_w * dbus_w;

    type rbus_type is array(0 to module_count) of std_logic_vector(rbus_w - 1 downto 0); -- 0 is reserved for no module.
    type sbus_type is array(0 to module_count) of std_logic_vector(sbus_w - 1 downto 0);

    constant clk_freq   :   integer := 200_000_000; -- Clock frequency in Hz.
    constant baudrate   :   integer := 57600; -- Baudrate for the UART.

    type signal_array is array(natural range <>) of std_logic_vector(15 downto 0); -- Used in the router.
end package mypak;