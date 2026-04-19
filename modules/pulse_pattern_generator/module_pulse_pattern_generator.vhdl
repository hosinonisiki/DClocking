-- ///////////////Documentation////////////////////
-- Bus wrapper for the pulse pattern generator module.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity module_pulse_pattern_generator is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        bus_en_in       :   in  std_logic;
        dbus_in         :   in  std_logic_vector(dbus_w - 1 downto 0);
        abus_in         :   in  std_logic_vector(abus_w - 1 downto 0);
        cbus_in         :   in  std_logic_vector(cbus_w - 1 downto 0);
        rsp_data_out    :   out std_logic_vector(rdbus_w - 1 downto 0);
        rsp_stat_out    :   out std_logic_vector(rsbus_w - 1 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity module_pulse_pattern_generator;

architecture structural of module_pulse_pattern_generator is
    signal core_param       :   std_logic_vector(1023 downto 0) := (others => '0');
    signal core_rst         :   std_logic := '1';

    signal ram_rst          :   std_logic := '1';
    signal handler_rst      :   std_logic := '1';

    signal wdata            :   std_logic_vector(dbus_w - 1 downto 0);
    signal waddr            :   std_logic_vector(abus_w - 1 downto 0);
    signal wmask            :   std_logic_vector(dbus_w - 1 downto 0);
    signal wval             :   std_logic;
    signal wen              :   std_logic;
    signal rdata            :   std_logic_vector(dbus_w - 1 downto 0);
    signal raddr            :   std_logic_vector(abus_w - 1 downto 0);
    signal rval             :   std_logic;
    signal ren              :   std_logic;
begin
    core_entity : entity work.pulse_pattern_generator generic map(
        io_buf => buf_for_io
    ) port map(
        clk             =>  clk,
        rst             =>  core_rst,
        core_param_in   =>  core_param,
        sig_out         =>  sig_out
    );

    parameter_ram : entity work.parameter_ram_1024 generic map(
        ram_default     =>  x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000"
    ) port map(
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
