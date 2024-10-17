-- ///////////////Documentation////////////////////
-- This file describes a general template for modules
-- that are to be plugged into the top architecture.
-- The template contains an entity that describes the
-- core function of the module. A bus handler is used
-- to handle data from the bus and implement custom
-- logic. Also, a custom ram-like module is used to
-- store parameters for the core module.

-- Substitute core entity, default parameters, and data
-- flow ports with the actual module implementation.
-- Also substitute the bus handler if specific logic
-- is needed.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity module_pid_controller is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        bus_en_in       :   in  std_logic;
        dbus_in         :   in  std_logic_vector(dbus_w - 1 downto 0);
        abus_in         :   in  std_logic_vector(abus_w - 1 downto 0);
        cbus_in         :   in  std_logic_vector(cbus_w - 1 downto 0);
        rsp_data_out    :   out std_logic_vector(rdbus_w - 1 downto 0);
        rsp_stat_out    :   out std_logic_vector(rsbus_w - 1 downto 0);
        -- data flow ports
        error_in        :   in  std_logic_vector(15 downto 0);
        feedback_out    :   out std_logic_vector(15 downto 0)
    );
end entity module_pid_controller;

architecture structural of module_pid_controller is
    signal core_param       :   std_logic_vector(255 downto 0) := (others => '0'); -- Storing all parameters and control bits for the core module
    signal core_rst         :   std_logic := '1';

    signal ram_rst          :   std_logic := '1';
    signal handler_rst      :   std_logic := '1';

    signal wdata            :   std_logic_vector(dbus_w - 1 downto 0); -- Data to be written to the ram
    signal waddr            :   std_logic_vector(abus_w - 1 downto 0); -- Address to write to
    signal wmask            :   std_logic_vector(dbus_w - 1 downto 0); -- Data mask
    signal wval             :   std_logic; -- Valid signal
    signal wen              :   std_logic; -- Write enable signal. The writing process starts as soon as wen is active, but the data is only written once wval is active. 
                                       -- This is to make sure that parameters longer than dbus_w are written simultaneously.
    signal rdata            :   std_logic_vector(dbus_w - 1 downto 0); -- Data read from the ram
    signal raddr            :   std_logic_vector(abus_w - 1 downto 0); -- Address to read from
    signal rval             :   std_logic; -- Valid signal, active when the data is ready
    signal ren              :   std_logic; -- Read enable signal
begin
    
    core_entity : entity work.pid_controller generic map(
        -- Removed buffer options for high bandwidth testing
        io_buf => buf_none    
    )port map(
        clk             =>  clk,
        rst             =>  core_rst,
        core_param_in   =>  core_param,
        -- data flow ports
        error_in        =>  error_in,
        feedback_out    =>  feedback_out
    );

    parameter_ram : entity work.parameter_ram_256 generic map(
        ram_default     =>  x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000"
    )port map(
        clk             =>  clk,
        rst             =>  ram_rst,
        wdata_in        =>  wdata,
        waddr_in        =>  waddr,
        wmask_in        =>  wmask,
        wval_in         =>  wval,
        wen_in          =>  wen,
        rdata_out       =>  rdata,
        raddr_in        =>  raddr,
        rval_out        =>  rval,
        ren_in          =>  ren,
        ram_data_out    =>  core_param
    );

    bus_handler : entity work.bus_handler port map(
        clk             =>  clk,
        rst             =>  handler_rst,
        bus_en_in       =>  bus_en_in,
        dbus_in         =>  dbus_in,
        abus_in         =>  abus_in,
        cbus_in         =>  cbus_in,
        rsp_data_out    =>  rsp_data_out,
        rsp_stat_out    =>  rsp_stat_out,
        wdata_out       =>  wdata,
        waddr_out       =>  waddr,
        wmask_out       =>  wmask,
        wval_out        =>  wval,
        wen_out         =>  wen,
        rdata_in        =>  rdata,
        raddr_out       =>  raddr,
        rval_in         =>  rval,
        ren_out         =>  ren,
        ram_rst_out     =>  ram_rst,
        core_rst_out    =>  core_rst
    );
    handler_rst <= rst;

end architecture structural;