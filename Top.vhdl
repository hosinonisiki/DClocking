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

    module_7_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_FIRF_ADDR else '0'; -- constant defined in mypak
        module_7 : entity work.module_fir_filter port map(
            clk             =>  clk,
            rst             =>  mod_rst(7),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(7),
            rsp_stat_out    =>  rsbus(7),
            
            sig_in          => sig_bank_out(11),
            sig_out         => sig_bank_in(15)
        );
    end block module_7_block;

    module_8_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_MIXR_ADDR else '0'; -- constant defined in mypak
        module_8 : entity work.module_mixer port map(
            clk             =>  clk,
            rst             =>  mod_rst(8),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(8),
            rsp_stat_out    =>  rsbus(8),
            
            sig_a_in        => sig_bank_out(12),
            sig_b_in        => sig_bank_out(13),
            sig_out         => sig_bank_in(16)
        );
    end block module_8_block;

    module_9_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_SCL2_ADDR else '0'; -- constant defined in mypak
        module_9 : entity work.module_scaler port map(
            clk             =>  clk,
            rst             =>  mod_rst(9),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(9),
            rsp_stat_out    =>  rsbus(9),
            
            sig_in         => sig_bank_out(14),
            sig_out        => sig_bank_in(17)
        );
    end block module_9_block;

    module_10_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_SCL3_ADDR else '0'; -- constant defined in mypak
        module_10 : entity work.module_scaler port map(
            clk             =>  clk,
            rst             =>  mod_rst(10),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(10),
            rsp_stat_out    =>  rsbus(10),
            
            sig_in         => sig_bank_out(15),
            sig_out        => sig_bank_in(18)
        );
    end block module_10_block;

    module_11_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_SCL4_ADDR else '0'; -- constant defined in mypak
        module_11 : entity work.module_scaler port map(
            clk             =>  clk,
            rst             =>  mod_rst(11),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(11),
            rsp_stat_out    =>  rsbus(11),
            
            sig_in         => sig_bank_out(16),
            sig_out        => sig_bank_in(19)
        );
    end block module_11_block;

    module_12_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_ATAN_ADDR else '0'; -- constant defined in mypak
        module_12 : entity work.module_inv_trigonometric port map(
            clk             =>  clk,
            rst             =>  mod_rst(12),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(12),
            rsp_stat_out    =>  rsbus(12),
            
            sin_in         => sig_bank_out(17),
            cos_in         => sig_bank_out(18),
            phase_out      => sig_bank_in(20)
        );
    end block module_12_block;

    module_13_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_FIR2_ADDR else '0'; -- constant defined in mypak
        module_13 : entity work.module_fir_filter port map(
            clk             =>  clk,
            rst             =>  mod_rst(13),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(13),
            rsp_stat_out    =>  rsbus(13),
            
            sig_in          => sig_bank_out(19),
            sig_out         => sig_bank_in(21)
        );
    end block module_13_block;

    module_14_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_MIX2_ADDR else '0'; -- constant defined in mypak
        module_14 : entity work.module_mixer port map(
            clk             =>  clk,
            rst             =>  mod_rst(14),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(14),
            rsp_stat_out    =>  rsbus(14),
            
            sig_a_in        => sig_bank_out(20),
            sig_b_in        => sig_bank_out(21),
            sig_out         => sig_bank_in(22)
        );
    end block module_14_block;

    module_15_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_UNWR_ADDR else '0'; -- constant defined in mypak
        module_15 : entity work.module_unwrapper port map(
            clk             =>  clk,
            rst             =>  mod_rst(15),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(15),
            rsp_stat_out    =>  rsbus(15),
            
            sig_in          => sig_bank_out(22),
            sig_out         => sig_bank_in(23),

            auto_reset_in   => ctrl_bank_out(2)
        );
    end block module_15_block;

    module_16_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_TRI2_ADDR else '0'; -- constant defined in mypak
        module_16 : entity work.module_trigonometric port map(
            clk             =>  clk,
            rst             =>  mod_rst(16),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(16),
            rsp_stat_out    =>  rsbus(16),
            
            phase_in        =>  sig_bank_out(23),
            sin_out         =>  sig_bank_in(24),
            cos_out         =>  sig_bank_in(25)
        );
    end block module_16_block;

    module_17_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_ACC2_ADDR else '0'; -- constant defined in mypak
        module_17 : entity work.module_accumulator port map(
            clk             =>  clk,
            rst             =>  mod_rst(17),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(17),
            rsp_stat_out    =>  rsbus(17),
            
            acc_out         =>  sig_bank_in(26),

            auto_reset_in   =>  ctrl_bank_out(3)
        );
    end block module_17_block;

    module_18_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_PID2_ADDR else '0'; -- constant defined in mypak
        module_18 : entity work.module_pid_controller port map(
            clk             =>  clk,
            rst             =>  mod_rst(18),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(18),
            rsp_stat_out    =>  rsbus(18),
            
            error_in        => sig_bank_out(24),
            feedback_out    => sig_bank_in(27),

            auto_reset_in   => ctrl_bank_out(4)
        );
    end block module_18_block;

    module_19_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_LTRN_ADDR else '0'; -- constant defined in mypak
        module_19 : entity work.module_linear_transformer port map(
            clk             =>  clk,
            rst             =>  mod_rst(19),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(19),
            rsp_stat_out    =>  rsbus(19),
            
            sig_a_in        => sig_bank_out(25),
            sig_b_in        => sig_bank_out(26),
            sig_a_out       => sig_bank_in(28),
            sig_b_out       => sig_bank_in(29)
        );
    end block module_19_block;

    module_20_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_LTR2_ADDR else '0'; -- constant defined in mypak
        module_20 : entity work.module_linear_transformer port map(
            clk             =>  clk,
            rst             =>  mod_rst(20),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(20),
            rsp_stat_out    =>  rsbus(20),
            
            sig_a_in        => sig_bank_out(27),
            sig_b_in        => sig_bank_out(28),
            sig_a_out       => sig_bank_in(30),
            sig_b_out       => sig_bank_in(31)
        );
    end block module_20_block;

    module_21_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_MIX3_ADDR else '0'; -- constant defined in mypak
        module_21 : entity work.module_mixer port map(
            clk             =>  clk,
            rst             =>  mod_rst(21),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(21),
            rsp_stat_out    =>  rsbus(21),
            
            sig_a_in        => sig_bank_out(29),
            sig_b_in        => sig_bank_out(30),
            sig_out         => sig_bank_in(32)
        );
    end block module_21_block;

    module_22_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_MIX4_ADDR else '0'; -- constant defined in mypak
        module_22 : entity work.module_mixer port map(
            clk             =>  clk,
            rst             =>  mod_rst(22),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(22),
            rsp_stat_out    =>  rsbus(22),
            
            sig_a_in        => sig_bank_out(31),
            sig_b_in        => sig_bank_out(32),
            sig_out         => sig_bank_in(33)
        );
    end block module_22_block;

    module_23_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_FIR3_ADDR else '0'; -- constant defined in mypak
        module_23 : entity work.module_fir_filter port map(
            clk             =>  clk,
            rst             =>  mod_rst(23),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(23),
            rsp_stat_out    =>  rsbus(23),
            
            sig_in          => sig_bank_out(33),
            sig_out         => sig_bank_in(34)
        );
    end block module_23_block;

    module_24_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_FIR4_ADDR else '0'; -- constant defined in mypak
        module_24 : entity work.module_fir_filter port map(
            clk             =>  clk,
            rst             =>  mod_rst(24),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(24),
            rsp_stat_out    =>  rsbus(24),
            
            sig_in          => sig_bank_out(34),
            sig_out         => sig_bank_in(35)
        );
    end block module_24_block;

    module_25_block : block
        signal bus_en       :   std_logic;
    begin
        bus_en <= '1' when mbus = BUS_ATA2_ADDR else '0'; -- constant defined in mypak
        module_25 : entity work.module_inv_trigonometric port map(
            clk             =>  clk,
            rst             =>  mod_rst(25),
            bus_en_in       =>  bus_en,
            dbus_in         =>  dbus,
            abus_in         =>  abus,
            cbus_in         =>  cbus,
            rsp_data_out    =>  rdbus(25),
            rsp_stat_out    =>  rsbus(25),
            
            sin_in         => sig_bank_out(35),
            cos_in         => sig_bank_out(36),
            phase_out      => sig_bank_in(36)
        );
    end block module_25_block;

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