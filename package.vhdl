-- ///////////////Documentation////////////////////
-- Package for global defined constants.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mypak is
    constant dbus_w     :   integer := 32; -- Width of the data bus.
    constant abus_w     :   integer := 5; -- Width of the address bus. This determines the size of individual memories in each module.
    constant mbus_w     :   integer := 8; -- Width of the module selection bus. This determines the max number of modules that can be connected to the bus.
    constant cbus_w     :   integer := 8; -- Width of the control bus.
    constant rbus_w     :   integer := 32; -- Width of the response bus.
    constant sbus_w     :   integer := 8; -- Width of the response status bus.

    constant clk_freq   :   integer := 200_000_000; -- Clock frequency in Hz.
end package mypak;