-- ///////////////Documentation////////////////////
-- This design is the main control unit of the system.
-- It involves an entity containing control logic,
-- a uart receiver and a transmitter, along with
-- two fifo buffers.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity main_control is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        txd_out         :   out std_logic;
        rxd_in          :   in  std_logic;
        err_out         :   out std_logic;
        mosi_out        :   out std_logic;
        miso_in         :   in  std_logic;
        sclk_out        :   out std_logic;
        ss_out          :   out std_logic_vector(0 to 15);
        io_tri_out      :   out std_logic;
        dbus_out        :   out std_logic_vector(dbus_w - 1 downto 0);
        abus_out        :   out std_logic_vector(abus_w - 1 downto 0);
        mbus_out        :   out std_logic_vector(mbus_w - 1 downto 0);
        cbus_out        :   out std_logic_vector(cbus_w - 1 downto 0);
        rsp_sel_out     :   out std_logic_vector(mbus_w - 1 downto 0);
        rsp_data_in     :   in  std_logic_vector(rdbus_w - 1 downto 0);
        rsp_stat_in     :   in  std_logic_vector(rsbus_w - 1 downto 0)
    );
end entity main_control;

architecture structural of main_control is
    signal axi_aresetn  :   std_logic;
    signal irpt         :   std_logic;
    signal axi_awaddr   :   std_logic_vector(31 downto 0);
    signal axi_awvalid  :   std_logic;
    signal axi_awready  :   std_logic;
    signal axi_wdata    :   std_logic_vector(31 downto 0);
    signal axi_wstrb    :   std_logic_vector(3 downto 0);
    signal axi_wvalid   :   std_logic;
    signal axi_wready   :   std_logic;
    signal axi_bresp    :   std_logic_vector(1 downto 0);
    signal axi_bvalid   :   std_logic;
    signal axi_bready   :   std_logic;
    signal axi_araddr   :   std_logic_vector(31 downto 0);
    signal axi_arvalid  :   std_logic;
    signal axi_arready  :   std_logic;
    signal axi_rdata    :   std_logic_vector(31 downto 0);
    signal axi_rresp    :   std_logic_vector(1 downto 0);
    signal axi_rvalid   :   std_logic;
    signal axi_rready   :   std_logic;

    signal rx_ren       :   std_logic;
    signal rx_empty     :   std_logic;
    signal rx_char      :   std_logic_vector(7 downto 0);

    signal tx_wen       :   std_logic;
    signal tx_full      :   std_logic;
    signal tx_char      :   std_logic_vector(7 downto 0); -- Data read from control logic and sent to fifo

    signal spi_rst      :   std_logic;
    signal spi_ss_bin   :   std_logic_vector(3 downto 0); -- Binary spi ss signal
    signal spi_en       :   std_logic;
    signal spi_control  :   std_logic_vector(31 downto 0);
    signal spi_txd      :   std_logic_vector(31 downto 0);
    signal spi_rxd      :   std_logic_vector(31 downto 0);
    signal spi_val      :   std_logic;
    signal spi_idle     :   std_logic;

    signal cc_rst       :   std_logic;

    -- Instantiating Vivado IPs in this design.
    COMPONENT axi_uart16550_0
        PORT (
            s_axi_aclk : IN STD_LOGIC;
            s_axi_aresetn : IN STD_LOGIC;
            ip2intc_irpt : OUT STD_LOGIC;
            freeze : IN STD_LOGIC;
            s_axi_awaddr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
            s_axi_awvalid : IN STD_LOGIC;
            s_axi_awready : OUT STD_LOGIC;
            s_axi_wdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            s_axi_wstrb : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
            s_axi_wvalid : IN STD_LOGIC;
            s_axi_wready : OUT STD_LOGIC;
            s_axi_bresp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            s_axi_bvalid : OUT STD_LOGIC;
            s_axi_bready : IN STD_LOGIC;
            s_axi_araddr : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
            s_axi_arvalid : IN STD_LOGIC;
            s_axi_arready : OUT STD_LOGIC;
            s_axi_rdata : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
            s_axi_rresp : OUT STD_LOGIC_VECTOR(1 DOWNTO 0);
            s_axi_rvalid : OUT STD_LOGIC;
            s_axi_rready : IN STD_LOGIC;
            baudoutn : OUT STD_LOGIC;
            ctsn : IN STD_LOGIC;
            dcdn : IN STD_LOGIC;
            ddis : OUT STD_LOGIC;
            dsrn : IN STD_LOGIC;
            dtrn : OUT STD_LOGIC;
            out1n : OUT STD_LOGIC;
            out2n : OUT STD_LOGIC;
            rin : IN STD_LOGIC;
            rtsn : OUT STD_LOGIC;
            rxrdyn : OUT STD_LOGIC;
            sin : IN STD_LOGIC;
            sout : OUT STD_LOGIC;
            txrdyn : OUT STD_LOGIC 
        );
    END COMPONENT;

    COMPONENT uart_custom_axi_master_0
        PORT (
            rst : IN STD_LOGIC;
            rst_busy : OUT STD_LOGIC;
            rxd_out : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
            rxen_in : IN STD_LOGIC;
            rxemp_out : OUT STD_LOGIC;
            txd_in : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
            txen_in : IN STD_LOGIC;
            txful_out : OUT STD_LOGIC;
            irpt : IN STD_LOGIC;
            err : OUT STD_LOGIC;
            m00_axi_aclk : IN STD_LOGIC;
            m00_axi_aresetn : IN STD_LOGIC;
            m00_axi_awaddr : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
            m00_axi_awprot : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
            m00_axi_awvalid : OUT STD_LOGIC;
            m00_axi_awready : IN STD_LOGIC;
            m00_axi_wdata : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
            m00_axi_wstrb : OUT STD_LOGIC_VECTOR(3 DOWNTO 0);
            m00_axi_wvalid : OUT STD_LOGIC;
            m00_axi_wready : IN STD_LOGIC;
            m00_axi_bresp : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            m00_axi_bvalid : IN STD_LOGIC;
            m00_axi_bready : OUT STD_LOGIC;
            m00_axi_araddr : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
            m00_axi_arprot : OUT STD_LOGIC_VECTOR(2 DOWNTO 0);
            m00_axi_arvalid : OUT STD_LOGIC;
            m00_axi_arready : IN STD_LOGIC;
            m00_axi_rdata : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
            m00_axi_rresp : IN STD_LOGIC_VECTOR(1 DOWNTO 0);
            m00_axi_rvalid : IN STD_LOGIC;
            m00_axi_rready : OUT STD_LOGIC 
        );
    END COMPONENT;

begin
    axi_aresetn <= not rst;

    uart : axi_uart16550_0 PORT MAP (
        s_axi_aclk => clk,
        s_axi_aresetn => axi_aresetn,
        ip2intc_irpt => irpt,
        freeze => '0',
        s_axi_awaddr => axi_awaddr(12 downto 0),
        s_axi_awvalid => axi_awvalid,
        s_axi_awready => axi_awready,
        s_axi_wdata => axi_wdata,
        s_axi_wstrb => axi_wstrb,
        s_axi_wvalid => axi_wvalid,
        s_axi_wready => axi_wready,
        s_axi_bresp => axi_bresp,
        s_axi_bvalid => axi_bvalid,
        s_axi_bready => axi_bready,
        s_axi_araddr => axi_araddr(12 downto 0),
        s_axi_arvalid => axi_arvalid,
        s_axi_arready => axi_arready,
        s_axi_rdata => axi_rdata,
        s_axi_rresp => axi_rresp,
        s_axi_rvalid => axi_rvalid,
        s_axi_rready => axi_rready,
        baudoutn => open,
        ctsn => '0',
        dcdn => '0',
        ddis => open,
        dsrn => '0',
        dtrn => open,
        out1n => open,
        out2n => open,
        rin => '1',
        rtsn => open,
        rxrdyn => open,
        sin => rxd_in,
        sout => txd_out,
        txrdyn => open
    );

    uart_axi_master : uart_custom_axi_master_0 PORT MAP (
        rst => rst,
        rst_busy => open,
        rxd_out => rx_char,
        rxen_in => rx_ren,
        rxemp_out => rx_empty,
        txd_in => tx_char,
        txen_in => tx_wen,
        txful_out => tx_full,
        irpt => irpt,
        err => err_out,
        m00_axi_aclk => clk,
        m00_axi_aresetn => axi_aresetn,
        m00_axi_awaddr => axi_awaddr,
        m00_axi_awprot => open,
        m00_axi_awvalid => axi_awvalid,
        m00_axi_awready => axi_awready,
        m00_axi_wdata => axi_wdata,
        m00_axi_wstrb => axi_wstrb,
        m00_axi_wvalid => axi_wvalid,
        m00_axi_wready => axi_wready,
        m00_axi_bresp => axi_bresp,
        m00_axi_bvalid => axi_bvalid,
        m00_axi_bready => axi_bready,
        m00_axi_araddr => axi_araddr,
        m00_axi_arprot => open,
        m00_axi_arvalid => axi_arvalid,
        m00_axi_arready => axi_arready,
        m00_axi_rdata => axi_rdata,
        m00_axi_rresp => axi_rresp,
        m00_axi_rvalid => axi_rvalid,
        m00_axi_rready => axi_rready
    );

    spi_trx : entity work.spi_trx generic map(
        cpol => '0',
        cpha => '0'
    )port map(
        clk         =>  clk,
        rst         =>  spi_rst,
        spi_en_in   =>  spi_en,
        ss_in       =>  spi_ss_bin,
        ss_out      =>  ss_out,
        mosi        =>  mosi_out,
        miso        =>  miso_in,
        sclk_out    =>  sclk_out,
        control_in  =>  spi_control,
        io_tri_out  =>  io_tri_out,
        din         =>  spi_txd,
        dout        =>  spi_rxd,
        dval_out    =>  spi_val,
        idle_out    =>  spi_idle
    );
    spi_rst <= rst;

    central_control : entity work.central_control port map(
        clk             =>  clk,
        rst             =>  cc_rst,
        rxd_in          =>  rx_char,
        rxen_out        =>  rx_ren,
        rxemp_in        =>  rx_empty,
        txd_out         =>  tx_char,
        txen_out        =>  tx_wen,
        txful_in        =>  tx_full,
        spi_ss_out      =>  spi_ss_bin,
        spi_en_out      =>  spi_en,
        spi_control_out =>  spi_control,
        spi_txd_out     =>  spi_txd,
        spi_rxd_in      =>  spi_rxd,
        spi_val_in      =>  spi_val,
        rsp_sel_out     =>  rsp_sel_out,
        rsp_data_in     =>  rsp_data_in,
        rsp_stat_in     =>  rsp_stat_in,
        dbus_out        =>  dbus_out,
        abus_out        =>  abus_out,
        mbus_out        =>  mbus_out,
        cbus_out        =>  cbus_out
    );
    cc_rst <= rst;
end architecture structural;