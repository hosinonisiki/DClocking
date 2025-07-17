-- ///////////////Documentation////////////////////
-- Package for global defined constants and functions.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mypak is
    constant is_debug   :   std_logic := '1'; -- Debug mode flag.


    type buf_type is (buf_for_io, buf_i_only, buf_o_only, buf_none); -- Universal io buffer type for the core modules.

    constant dbus_w     :   integer := 32; -- Width of the data bus.
    constant abus_w     :   integer := 6; -- Width of the address bus. This determines the size of individual memories in each module.
    constant mbus_w     :   integer := 5; -- Width of the module selection bus. This determines the max number of modules that can be connected to the bus.
    constant cbus_w     :   integer := 5; -- Width of the control bus.
    constant rdbus_w    :   integer := 32; -- Width of the response data bus.
    constant rsbus_w    :   integer := 3; -- Width of the response status bus.
    constant core_param_size : integer := 2 ** abus_w * dbus_w; -- Upper limit of ram size for each module.

    constant log_dbus_w :   integer := 5; -- Log2 of the data bus width.

    constant module_count   : integer := 6; -- Number of modules connected to the bus.
    constant BUS_ROUT_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(1, mbus_w)); -- Address of the router module.
    constant BUS_TRIG_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(2, mbus_w)); -- Address of the trigonometric module.
    constant BUS_ACCM_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(3, mbus_w)); -- Address of the accumulator module.
    constant BUS_SCLR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(4, mbus_w)); -- Address of the scalar module.
    constant BUS_MMWR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(5, mbus_w)); -- Address of the mim_wrapper module.
    constant BUS_PIDC_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(6, mbus_w)); -- Address of the PID controller module.

    -- Used in wrapper and central_control
    constant SPI_P1C1_ADDR      : integer := 0; -- Address of chip 1 on FMC Port 1.
    constant SPI_P1C2_ADDR      : integer := 1; -- Address of chip 2 on FMC Port 1.
    constant SPI_P1C3_ADDR      : integer := 2; -- Address of chip 3 on FMC Port 1.
    constant SPI_P1C4_ADDR      : integer := 3; -- Address of chip 4 on FMC Port 1.
    constant SPI_P2C1_ADDR      : integer := 4; -- Address of chip 1 on FMC Port 2.
    constant SPI_P2C2_ADDR      : integer := 5; -- Address of chip 2 on FMC Port 2.
    constant SPI_P2C3_ADDR      : integer := 6; -- Address of chip 3 on FMC Port 2.
    constant SPI_P2C4_ADDR      : integer := 7; -- Address of chip 4 on FMC Port 2.
    constant SPI_P3C1_ADDR      : integer := 8; -- Address of chip 1 on FMC Port 3.
    constant SPI_P3C2_ADDR      : integer := 9; -- Address of chip 2 on FMC Port 3.
    constant SPI_P3C3_ADDR      : integer := 10; -- Address of chip 3 on FMC Port 3.
    constant SPI_P3C4_ADDR      : integer := 11; -- Address of chip 4 on FMC Port 3.
    constant SPI_P4C1_ADDR      : integer := 12; -- Address of chip 1 on FMC Port 4.
    constant SPI_P4C2_ADDR      : integer := 13; -- Address of chip 2 on FMC Port 4.
    constant SPI_P4C3_ADDR      : integer := 14; -- Address of chip 3 on FMC Port 4.
    constant SPI_P4C4_ADDR      : integer := 15; -- Address of chip 4 on FMC Port 4.

    type rdbus_type is array(0 to module_count) of std_logic_vector(rdbus_w - 1 downto 0); -- 0 is reserved for no module.
    type rsbus_type is array(0 to module_count) of std_logic_vector(rsbus_w - 1 downto 0);

    constant clk_freq       :   integer := 250_000_000; -- Clock frequency in Hz.
    constant baudrate       :   integer := 19200; -- Baudrate for the UART.
    -- constant baudrate       :   integer := 3_906_250; -- Only use in simulation.

    constant spi_clk_freq   :   integer := 10_000_000; -- SPI clock frequency in Hz.

    type signal_array is array(natural range <>) of std_logic_vector(15 downto 0); -- Used in the router's io ports and mim_wrapper and top interface.

    function ceillog2(n : natural) return natural;
    function triangular(n : natural) return natural;
end package mypak;

package body mypak is
    function ceillog2(n : natural) return natural is
        variable result : natural := 0;
    begin
        assert n >= 1;
        while (2 ** result < n) loop
            result := result + 1;
        end loop;
        return result;
    end function;

    function triangular(n : natural) return natural is
    begin
        assert n >= 1;
        return (n * (n - 1)) / 2;
    end function;
end package body mypak;