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
-- dac : FL9781 14 bit

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity top is
    generic(
        ADC_channel_count   : integer := 4; -- Number of ADC channels
        DAC_channel_count   : integer := 4  -- Number of DAC channels
    );
    port(
        clk         :   in  std_logic;
        rst         :   in  std_logic;
        txd         :   out std_logic;
        rxd         :   in  std_logic;
        err         :   out std_logic;

        mosi        :   out std_logic;
        miso        :   in  std_logic;
        sclk        :   out std_logic;
        ss          :   out std_logic_vector(0 to 15);
        io_tri      :   out std_logic;

        adc_in      :   in  signal_array(0 to ADC_channel_count - 1); -- ADC input signals

        dac_out     :   out signal_array(0 to DAC_channel_count - 1) -- DAC output signals
    );
    attribute dont_touch : string;
    attribute dont_touch of top : entity is "true";
end entity top;

architecture structural of top is
    signal mc_rst       :   std_logic; -- main control reset
    signal mod_rst      :   std_logic_vector(1 to module_count); -- module reset

    -- Bus width defined in mypak
    signal dbus         :   std_logic_vector(dbus_w - 1 downto 0) := (others => '0'); -- data bus
    signal abus         :   std_logic_vector(abus_w - 1 downto 0) := (others => '0'); -- address bus
    signal mbus         :   std_logic_vector(mbus_w - 1 downto 0) := (others => '0'); -- module selection bus, x"00" refers to no module selected
    signal cbus         :   std_logic_vector(cbus_w - 1 downto 0) := (others => '0'); -- control bus

    signal rdbus        :   rdbus_type := (others => (others => '0')); -- response data bus
    signal rsbus        :   rsbus_type := (others => (others => '0')); -- response status bus

    signal rsp_sel      :   std_logic_vector(mbus_w - 1 downto 0) := (others => '0'); -- response select
    signal rsp_data     :   std_logic_vector(rdbus_w - 1 downto 0) := (others => '0'); -- response data from sub modules
    signal rsp_stat     :   std_logic_vector(rsbus_w - 1 downto 0) := (others => '0'); -- response status from sub modules

    signal adc          :   signal_array(0 to ADC_channel_count - 1) := (others => (others => '0')); -- ADC input signals

    signal dac          :   signal_array(0 to DAC_channel_count - 1) := (others => (others => '0')); -- DAC output signals

    signal sig_bank_in      :   signal_array(63 downto 0) := (others => (others => '0'));
    signal sig_bank_out     :   signal_array(63 downto 0) := (others => (others => '0'));
    signal ctrl_bank_in     :   std_logic_vector(63 downto 0) := (others => '0');
    signal ctrl_bank_out    :   std_logic_vector(63 downto 0) := (others => '0');
begin
    assert ADC_channel_count <= 8 and DAC_channel_count <= 8
        report "ADC and DAC channel count must be less than or equal to 8"
        severity failure;
        
    -- The main control module handles all ios and communication with the modules.
    main_control : entity work.main_control port map(
        clk             =>  clk,
        rst             =>  mc_rst,
        txd_out         =>  txd,
        rxd_in          =>  rxd,
        err_out         =>  err,

        mosi_out        =>  mosi,
        miso_in         =>  miso,
        sclk_out        =>  sclk,
        ss_out          =>  ss,
        io_tri_out      =>  io_tri,

        dbus_out        =>  dbus,
        abus_out        =>  abus,
        mbus_out        =>  mbus,
        cbus_out        =>  cbus,

        rsp_sel_out     =>  rsp_sel,
        rsp_data_in     =>  rsp_data,
        rsp_stat_in     =>  rsp_stat
    );
    mc_rst <= rst;

    response_mux : entity work.response_mux generic map(
        channel_count   =>  module_count   
    )port map(
        rdbus_in        =>  rdbus,
        rsbus_in        =>  rsbus,
        rsp_sel_in      =>  rsp_sel,
        rsp_data_out    =>  rsp_data,
        rsp_stat_out    =>  rsp_stat
    );



    mod_rst <= (others => rst);
    -- To register a module:
    -- 1.Follow the format below
    -- 2.Register the address of the module in mypak
    -- 3.Register the name of the module in uart_protocol
    -- 4.Add corresponding lines in central_control
    module_1_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_ROUT_ADDR else '0'; -- constant defined in mypak
        module_1 : entity work.module_signal_router(full) port map(
            clk             =>  clk,
            rst             =>  mod_rst(1),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(1),
            rsp_stat_out    =>  rsbus(1),
            
            sig_in          =>  sig_bank_in,
            sig_out         =>  sig_bank_out,
            ctrl_in         =>  ctrl_bank_in,
            ctrl_out        =>  ctrl_bank_out
        );
    end block module_1_block;

    module_2_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_TRIG_ADDR else '0'; -- constant defined in mypak
        module_2 : entity work.module_trigonometric port map(
            clk             =>  clk,
            rst             =>  mod_rst(2),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(2),
            rsp_stat_out    =>  rsbus(2),
            
            phase_in        =>  sig_bank_out(4),
            sin_out         =>  sig_bank_in(0),
            cos_out         =>  sig_bank_in(1)
        );
    end block module_2_block;

    module_3_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_ACCM_ADDR else '0'; -- constant defined in mypak
        module_3 : entity work.module_accumulator port map(
            clk             =>  clk,
            rst             =>  mod_rst(3),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(3),
            rsp_stat_out    =>  rsbus(3),
            
            acc_out         =>  sig_bank_in(4),

            auto_reset_in   =>  ctrl_bank_out(0)
        );
    end block module_3_block;

    module_4_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_SCLR_ADDR else '0'; -- constant defined in mypak
        module_4 : entity work.module_scaler port map(
            clk             =>  clk,
            rst             =>  mod_rst(4),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(4),
            rsp_stat_out    =>  rsbus(4),
            
            sig_out         =>  sig_bank_in(5),
            sig_in          =>  sig_bank_out(5)
        );
    end block module_4_block;

    module_5_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_MMWR_ADDR else '0'; -- constant defined in mypak
        module_5 : entity work.module_moku_mim_wrapper port map(
            clk             =>  clk,
            rst             =>  mod_rst(5),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(5),
            rsp_stat_out    =>  rsbus(5),
            
            inputa          => sig_bank_out(6),
            inputb          => sig_bank_out(7),
            inputc          => sig_bank_out(8),
            inputd          => sig_bank_out(9),
            outputa         => sig_bank_in(10),
            outputb         => sig_bank_in(11),
            outputc         => sig_bank_in(12),
            outputd         => sig_bank_in(13)
        );
    end block module_5_block;

    module_6_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_PIDC_ADDR else '0'; -- constant defined in mypak
        module_6 : entity work.module_pid_controller port map(
            clk             =>  clk,
            rst             =>  mod_rst(6),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(6),
            rsp_stat_out    =>  rsbus(6),
            
            error_in        => sig_bank_out(10),
            feedback_out    => sig_bank_in(14),

            auto_reset_in   => ctrl_bank_out(1)
        );
    end block module_6_block;

    -- signal banks provided by the router
    -- Last 8 channels reserved for top adc and dac ports
    
    adc_gen : for i in 0 to ADC_channel_count - 1 generate
        sig_bank_in(i + 56) <= adc(i);
    end generate;

    dac_gen : for i in 0 to DAC_channel_count - 1 generate
        dac(i) <= sig_bank_out(i + 56);
    end generate;

    -- analog front
    -- stage only the output
    process(clk)
    begin
        if rising_edge(clk) then
            dac_out <= dac;
        end if;
    end process;

    adc <= adc_in;
    
end architecture structural;