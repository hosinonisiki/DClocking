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

use work.moku_mim_config.all;

entity module_moku_mim_wrapper is
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
        inputa          :   in  std_logic_vector(15 downto 0);
        inputb          :   in  std_logic_vector(15 downto 0);
        inputc          :   in  std_logic_vector(15 downto 0);
        inputd          :   in  std_logic_vector(15 downto 0);
        outputa         :   out std_logic_vector(15 downto 0);
        outputb         :   out std_logic_vector(15 downto 0);
        outputc         :   out std_logic_vector(15 downto 0);
        outputd         :   out std_logic_vector(15 downto 0)
    );
end entity module_moku_mim_wrapper;

architecture structural of module_moku_mim_wrapper is
    signal core_param       :   std_logic_vector(2047 downto 0) := (others => '0'); -- Storing all parameters and control bits for the core module
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

    signal inputa_buf       :   signal_array(MAX_ID downto 0); -- Buffer for inputa
    signal inputb_buf       :   signal_array(MAX_ID downto 0); -- Buffer for inputb
    signal inputc_buf       :   signal_array(MAX_ID downto 0); -- Buffer for inputc
    signal inputd_buf       :   signal_array(MAX_ID downto 0); -- Buffer for inputd
    signal outputa_buf      :   signal_array(MAX_ID downto 0) := (others => (others => '0')); -- Buffer for outputa
    signal outputb_buf      :   signal_array(MAX_ID downto 0) := (others => (others => '0')); -- Buffer for outputb
    signal outputc_buf      :   signal_array(MAX_ID downto 0) := (others => (others => '0')); -- Buffer for outputc
    signal outputd_buf      :   signal_array(MAX_ID downto 0) := (others => (others => '0')); -- Buffer for outputd

    signal mim_en           :   std_logic;
    signal mim_id           :   std_logic_vector(5 downto 0);
begin
    core_entity_12 : entity work.moku_mim_wrapper(id_12) port map(
        clk             =>  clk,
        rst             =>  core_rst,
        core_param_in   =>  core_param,
        -- data flow ports
        inputa          =>  inputa_buf(12),
        inputb          =>  inputb_buf(12),
        inputc          =>  inputc_buf(12),
        inputd          =>  inputd_buf(12),
        outputa         =>  outputa_buf(12),
        outputb         =>  outputb_buf(12),
        outputc         =>  outputc_buf(12),
        outputd         =>  outputd_buf(12)
    );

    parameter_ram : entity work.parameter_ram_2048 generic map(
        ram_default     =>  x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &

                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &

                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &

                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
                            x"00000000000000000000000000000000" &
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

    bus_handler : entity work.bus_handler_moku_mim_wrapper port map(
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
        core_rst_out    =>  core_rst,
        -- Extra signals
        mim_en_out      =>  mim_en,
        mim_id_out      =>  mim_id
    );
    handler_rst <= rst;

    -- IO multiplexer
    input_buf_gen : for i in 0 to MAX_ID generate
        inputa_buf(i) <= inputa when mim_en = '1' and mim_id = std_logic_vector(to_unsigned(i, 6)) else (others => '0');
        inputb_buf(i) <= inputb when mim_en = '1' and mim_id = std_logic_vector(to_unsigned(i, 6)) else (others => '0');
        inputc_buf(i) <= inputc when mim_en = '1' and mim_id = std_logic_vector(to_unsigned(i, 6)) else (others => '0');
        inputd_buf(i) <= inputd when mim_en = '1' and mim_id = std_logic_vector(to_unsigned(i, 6)) else (others => '0');
    end generate input_buf_gen;
    outputa <= outputa_buf(to_integer(unsigned(mim_id))) when mim_en = '1' else (others => '0');
    outputb <= outputb_buf(to_integer(unsigned(mim_id))) when mim_en = '1' else (others => '0');
    outputc <= outputc_buf(to_integer(unsigned(mim_id))) when mim_en = '1' else (others => '0');
    outputd <= outputd_buf(to_integer(unsigned(mim_id))) when mim_en = '1' else (others => '0');
end architecture structural;