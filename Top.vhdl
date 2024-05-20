-- ///////////////Documentation////////////////////
-- This is a top down design of a complex feedback
-- control system. The system is designed to lock
-- the fr diff and fceo diff in a dual comb system.
-- The top level entity describes the i/o port,
-- which is connected to a uart/usb interface. The
-- design also describes a custom bus structure to
-- communicate between the different modules. The
-- modules are described in seperate files.

-- The bus employs a custom protocol. A module
-- selection bus is used to select the module to
-- communicate with. The address bus is used to
-- select the memory location in the module. The
-- data bus is used to write data to the module.
-- The control bus is used to send control signals.
-- The response bus is used to read data from the
-- module, as well as other status information.

-- All flags are high-active.

-- hardware types:
-- board : AXKU041
-- FPGA : XCKU040-FFVA1156-2-I
-- adc : FL9613 12 bit
-- dac : FL9781 16 bit

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity top is
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;
        txd         :   out std_logic;
        rxd         :   in  std_logic;

        adc_in_0    :   in  std_logic_vector(11 downto 0);
        adc_in_1    :   in  std_logic_vector(11 downto 0);
        adc_in_2    :   in  std_logic_vector(11 downto 0);
        adc_in_3    :   in  std_logic_vector(11 downto 0);

        dac_out_0   :   out std_logic_vector(15 downto 0);
        dac_out_1   :   out std_logic_vector(15 downto 0);
        dac_out_2   :   out std_logic_vector(15 downto 0);
        dac_out_3   :   out std_logic_vector(15 downto 0)
    );
end entity top;

architecture structural of top is
    signal mc_rst       :   std_logic; -- main control reset
    signal mod_rst      :   std_logic_vector(1 to module_count); -- module reset

    -- Bus width defined in mypak
    signal dbus         :   std_logic_vector(dbus_w - 1 downto 0) := (others => '0'); -- data bus
    signal abus         :   std_logic_vector(abus_w - 1 downto 0) := (others => '0'); -- address bus
    signal mbus         :   std_logic_vector(mbus_w - 1 downto 0) := (others => '0'); -- module selection bus, x"00" refers to no module selected
    signal cbus         :   std_logic_vector(cbus_w - 1 downto 0) := (others => '0'); -- control bus

    signal rbus         :   rbus_type := (others => (others => '0')); -- response bus
    signal sbus         :   sbus_type := (others => (others => '0')); -- response status bus

    SIGNAL rsp_sel      :   std_logic_vector(mbus_w - 1 downto 0) := (others => '0'); -- response select
    SIGNAL rsp          :   std_logic_vector(rbus_w - 1 downto 0) := (others => '0'); -- response from sub modules
    SIGNAL rsp_stat     :   std_logic_vector(sbus_w - 1 downto 0) := (others => '0'); -- response status from sub modules

    SIGNAL adc_0        :   std_logic_vector(11 downto 0) := x"000";
    SIGNAL adc_1        :   std_logic_vector(11 downto 0) := x"000";
    SIGNAL adc_2        :   std_logic_vector(11 downto 0) := x"000";
    SIGNAL adc_3        :   std_logic_vector(11 downto 0) := x"000";

    SIGNAL dac_0        :   std_logic_vector(15 downto 0) := x"0000";
    SIGNAL dac_1        :   std_logic_vector(15 downto 0) := x"0000";
    SIGNAL dac_2        :   std_logic_vector(15 downto 0) := x"0000";
    SIGNAL dac_3        :   std_logic_vector(15 downto 0) := x"0000";
begin

    -- The main control module handles all ios and communication with the modules.
    main_control : entity work.main_control port map(
        clk             =>  clk,
        rst             =>  mc_rst,
        txd_out         =>  txd,
        rxd_in          =>  rxd,
        dbus_out        =>  dbus,
        abus_out        =>  abus,
        mbus_out        =>  mbus,
        cbus_out        =>  cbus,

        rsp_sel_out     =>  rsp_sel,
        rsp_in          =>  rsp,
        rsp_stat_in     =>  rsp_stat
    );
    mc_rst <= rst;

    response_mux : entity work.response_mux generic map(
        channel_count   =>  module_count   
    )port map(
        rbus_in         =>  rbus,
        sbus_in         =>  sbus,
        rsp_sel_in      =>  rsp_sel,
        rsp_out         =>  rsp,
        rsp_stat_out    =>  rsp_stat
    );



    mod_rst <= (others => rst);
    -- register each module as the following
    module_1_block : block
        port(
            clk             :   in  std_logic;
            rst             :   in  std_logic;
            dbus_in         :   in  std_logic_vector(dbus_w - 1 downto 0);
            abus_in         :   in  std_logic_vector(abus_w - 1 downto 0);
            mbus_in         :   in  std_logic_vector(mbus_w - 1 downto 0);
            cbus_in         :   in  std_logic_vector(cbus_w - 1 downto 0);
            rsp_out         :   out std_logic_vector(rbus_w - 1 downto 0);
            rsp_stat_out    :   out std_logic_vector(sbus_w - 1 downto 0)
            -- data flow ports
        );
        port map(
            clk             =>  clk,
            rst             =>  mod_rst(1),
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            mbus_in         =>  mbus,
            cbus_in         =>  cbus,
            rsp_out         =>  rbus(1),
            rsp_stat_out    =>  sbus(1)
        );
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = x"01" else '0';

        module_1 : entity work.module_1 port map(
            clk             =>  clk,
            rst             =>  rst,
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus_in,
            abus_in         =>  abus_in,
            cbus_in         =>  cbus_in,
            rsp_out         =>  rsp_out,
            rsp_stat_out    =>  rsp_stat_out
        );
    end block module_1_block;



    -- analog front
    process(clk)
    begin
        if rising_edge(clk) then
            adc_0 <= adc_in_0;
            adc_1 <= adc_in_1;
            adc_2 <= adc_in_2;
            adc_3 <= adc_in_3;

            dac_out_0 <= dac_0;
            dac_out_1 <= dac_1;
            dac_out_2 <= dac_2;
            dac_out_3 <= dac_3;
        end if;
    end process;
    
end architecture structural;