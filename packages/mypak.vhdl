-- ///////////////Documentation////////////////////
-- Package for global defined constants and functions.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package mypak is
    constant is_debug   :   std_logic := '1'; -- Debug mode flag.


    type buf_type is (buf_for_io, buf_i_only, buf_o_only, buf_none); -- Universal io buffer type for the core modules.

    constant dbus_w     :   integer := 32; -- Width of the data bus.
    constant abus_w     :   integer := 7; -- Width of the address bus. This determines the size of individual memories in each module.
    constant mbus_w     :   integer := 5; -- Width of the module selection bus. This determines the max number of modules that can be connected to the bus.
    constant cbus_w     :   integer := 5; -- Width of the control bus.
    constant rdbus_w    :   integer := 32; -- Width of the response data bus.
    constant rsbus_w    :   integer := 3; -- Width of the response status bus.
    constant core_param_size : integer := 2 ** abus_w * dbus_w; -- Upper limit of ram size for each module.

    constant log_dbus_w :   integer := 5; -- Log2 of the data bus width.

    constant module_count   : integer := 27; -- Number of modules connected to the bus.
    constant BUS_ROUT_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(1, mbus_w)); -- Address of the router module.
    constant BUS_TRIG_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(2, mbus_w)); -- Address of the trigonometric module.
    constant BUS_ACCM_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(3, mbus_w)); -- Address of the accumulator module.
    constant BUS_SCLR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(4, mbus_w)); -- Address of the scalar module.
    constant BUS_MMWR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(5, mbus_w)); -- Address of the mim_wrapper module.
    constant BUS_PIDC_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(6, mbus_w)); -- Address of the PID controller module.
    constant BUS_FIRF_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(7, mbus_w)); -- Address of the FIR filter module.
    constant BUS_MIXR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(8, mbus_w)); -- Address of the mixer module.
    constant BUS_SCL2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(9, mbus_w)); -- Address of the 2nd scalar module.
    constant BUS_SCL3_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(10, mbus_w)); -- Address of the 3rd scalar module.
    constant BUS_SCL4_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(11, mbus_w)); -- Address of the 4th scalar module.
    constant BUS_ATAN_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(12, mbus_w)); -- Address of the inverse trigonometric module.
    constant BUS_FIR2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(13, mbus_w)); -- Address of the 2nd FIR filter module.
    constant BUS_MIX2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(14, mbus_w)); -- Address of the 2nd mixer module.
    constant BUS_UNWR_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(15, mbus_w)); -- Address of the unwrapper module.
    constant BUS_TRI2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(16, mbus_w)); -- Address of the 2nd trigonometric module.
    constant BUS_ACC2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(17, mbus_w)); -- Address of the 2nd accumulator module.
    constant BUS_PID2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(18, mbus_w)); -- Address of the 2nd PID controller module.
    constant BUS_LTRN_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(19, mbus_w)); -- Address of the linear transformer module.
    constant BUS_LTR2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(20, mbus_w)); -- Address of the 2nd linear transformer module.
    constant BUS_MIX3_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(21, mbus_w)); -- Address of the 3rd mixer module.
    constant BUS_MIX4_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(22, mbus_w)); -- Address of the 4th mixer module.
    constant BUS_FIR3_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(23, mbus_w)); -- Address of the 3rd FIR filter module.
    constant BUS_FIR4_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(24, mbus_w)); -- Address of the 4th FIR filter module.
    constant BUS_ATA2_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(25, mbus_w)); -- Address of the 2nd inverse trigonometric module.
    constant BUS_PDHS_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(26, mbus_w)); -- Address of the PDH state machine module.
    constant BUS_SCLO_ADDR     : std_logic_vector(mbus_w - 1 downto 0) := std_logic_vector(to_unsigned(27, mbus_w)); -- Address of the SCALO state machine module.

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
    constant baudrate       :   integer := 115200; -- Baudrate for the UART.
    -- constant baudrate       :   integer := 3_906_250; -- Only use in simulation.

    constant spi_clk_freq   :   integer := 1_000_000; -- SPI clock frequency in Hz.

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