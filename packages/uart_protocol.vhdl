-- ///////////////Documentation////////////////////
-- Package describing protocol for the communication
-- bwtween FPGA and PC. Each message is composed
-- of ASCII characters, each of which is sent through
-- a uart interface.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

package uart_protocol is
    -- Each constant starts with a 'u' to distinguish from bus protocol constants
    constant u_INIT      : std_logic_vector(7 downto 0) := x"3a"; -- ASCII ':', discard all cache and immediately start a new session
    constant u_TERM      : std_logic_vector(7 downto 0) := x"21"; -- ASCII '!', if a session is ongoing, terminate it and parse the cached string
    constant u_SEP       : std_logic_vector(7 downto 0) := x"2e"; -- ASCII '.', separates different parts of a message
    -- Each message sent from the PC to the FPGA is composed of several segments
    -- Each segment is composed of exactly 4 bytes
    -- Example:
    -- :SPI_.DAC1.<4B data>.<4B data>!
    -- :BUS_.ROUT.WRTE.ADDR.<4B data>.DATA.<4B data>.HOLD!
    -- :BUS_.ROUT.READ.ADDR.<4B data>.BYTE.<4B data>!
    -- :ACKN.<4B data>!
    -- :ERR_!

    constant u_SPACE_SPI    : std_logic_vector(31 downto 0) := x"5350495f"; -- ASCII 'SPI_'
        constant u_DEVICE_DAC1  : std_logic_vector(31 downto 0) := x"44414331"; -- ASCII 'DAC1'
        constant u_DEVICE_DAC2  : std_logic_vector(31 downto 0) := x"44414332"; -- ASCII 'DAC2'
        constant u_DEVICE_CLK1  : std_logic_vector(31 downto 0) := x"434c4b31"; -- ASCII 'CLK1'
        constant u_DEVICE_ADC1  : std_logic_vector(31 downto 0) := x"41444331"; -- ASCII 'ADC1'
        constant u_DEVICE_ADC2  : std_logic_vector(31 downto 0) := x"41444332"; -- ASCII 'ADC2'

    constant u_SPACE_BUS    : std_logic_vector(31 downto 0) := x"4255535f"; -- ASCII 'BUS_'
        constant u_DEVICE_ROUT  : std_logic_vector(31 downto 0) := x"524f5554"; -- ASCII 'ROUT'
        constant u_DEVICE_TRIG  : std_logic_vector(31 downto 0) := x"54524947"; -- ASCII 'TRIG'
        constant u_DEVICE_ACCM  : std_logic_vector(31 downto 0) := x"4143434d"; -- ASCII 'ACCM'
        constant u_DEVICE_SCLR  : std_logic_vector(31 downto 0) := x"53434c52"; -- ASCII 'SCLR'
        constant u_COMMAND_CTRL : std_logic_vector(31 downto 0) := x"4354524c"; -- ASCII 'CTRL'
            constant u_KEYWORD_SETC : std_logic_vector(31 downto 0) := x"53455443"; -- ASCII 'SETC'
            constant u_KEYWORD_SETR : std_logic_vector(31 downto 0) := x"53455452"; -- ASCII 'SETR'
            constant u_KEYWORD_RSTC : std_logic_vector(31 downto 0) := x"52535443"; -- ASCII 'RSTC'
            constant u_KEYWORD_RSTR : std_logic_vector(31 downto 0) := x"52535452"; -- ASCII 'RSTR'
        constant u_COMMAND_WRTE : std_logic_vector(31 downto 0) := x"57525445"; -- ASCII 'WRTE'
        constant u_COMMAND_READ : std_logic_vector(31 downto 0) := x"52454144"; -- ASCII 'READ'
            constant u_KEYWORD_ADDR : std_logic_vector(31 downto 0) := x"41444452"; -- ASCII 'ADDR'
            constant u_KEYWORD_DATA : std_logic_vector(31 downto 0) := x"44415441"; -- ASCII 'DATA'
            constant u_KEYWORD_MASK : std_logic_vector(31 downto 0) := x"4d41534b"; -- ASCII 'MASK'
            constant u_KEYWORD_HOLD : std_logic_vector(31 downto 0) := x"484f4c44"; -- ASCII 'HOLD'
        -- Further commands for the ethernet trx may be necessary
        -- since they can't be mapped to simple read/write operations.
        -- For example, the module should reject new transmission
        -- requests while the current one is ongoing. This also
        -- calls for custom bus handlers.

    constant u_RESPONSE_ACKN : std_logic_vector(31 downto 0) := x"41434b4e"; -- ASCII 'ACKN'
    constant u_RESPONSE_ERR  : std_logic_vector(31 downto 0) := x"4552525f"; -- ASCII 'ERR_'
end package uart_protocol;