-- ///////////////Documentation////////////////////
-- Package for bus protocol.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

package bus_protocol is
    -- Control signals from master to slave
    -- The COMMAND signals obey certain patterns according to their usage so that they can be decoded more easily
    -- The 2 MSBs indicates the type of command, and the rest indicates specific action
    -- Length of the command may vary in the future
    -- "00XXX" usage:
    --      control     address     data
    --  t-1 0           X           X
    --  t0  COMMAND     X           X
    --  t1  0           X           X
    constant CONTROL_HEAD : std_logic_vector(1 downto 0) := "00"; -- Commands starting with "00" are control commands
    constant SET_CORE : std_logic_vector(cbus_w - 3 downto 0) := "010"; -- Set rst of module's core to 0
    constant RST_CORE : std_logic_vector(cbus_w - 3 downto 0) := "011"; -- Set rst of module's core to 1
    constant SET_RAM : std_logic_vector(cbus_w - 3 downto 0) := "100"; -- Set rst of module's ram to 0
    constant RST_RAM : std_logic_vector(cbus_w - 3 downto 0) := "101"; -- Set rst of module's ram to 1
    -- "010XX" usage:
    --      control     address      data
    --  t-1 0           X            X
    --  t0  COMMAND     ADDRESS      DATA
    --  t1  0           X            X
    constant WRITE_HEAD : std_logic_vector(1 downto 0) := "01"; -- Commands starting with "01" are write commands
    constant WRITE : std_logic_vector(cbus_w - 3 downto 0) := "000"; -- Write DATA to ADDRESS, and immediately apply all changes
    constant WRITE_HOLD : std_logic_vector(cbus_w - 3 downto 0) := "001"; -- Write DATA to ADDRESS, but don't immediately apply it
    -- "011XX" usage:
    --      control     address      data
    --  t-1 0           X            X
    --  t0  COMMAND     ADDRESS      DATA1
    --  t1  0           X            DATA2
    --  t2  0           X            X
    constant WRITE_MASK : std_logic_vector(cbus_w - 3 downto 0) := "100"; -- Write DATA1 to ADDRESS, using DATA2 as mask, and immediately apply all changes
    constant WRITE_MASK_HOLD : std_logic_vector(cbus_w - 3 downto 0) := "101"; -- Write DATA1 to ADDRESS, using DATA2 as mask, but don't immediately apply it
    -- "10XXX" usage:
    --      control     address      data
    --  t-1 0           X            X
    --  t0  COMMAND     ADDRESS      X
    --  t1  0           X            X
    constant READ_HEAD : std_logic_vector(1 downto 0) := "10"; -- Commands starting with "10" are read commands
    constant READ : std_logic_vector(cbus_w - 3 downto 0) := "000"; -- Read from ADDRESS

    -- reply signals from slave to master
    constant ROGER : std_logic_vector(rsbus_w - 1 downto 0) := "001"; -- Acknowledge that the command was implemented
end package bus_protocol;