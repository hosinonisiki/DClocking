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
        dbus_out        :   out std_logic_vector(dbus_w - 1 downto 0);
        abus_out        :   out std_logic_vector(abus_w - 1 downto 0);
        mbus_out        :   out std_logic_vector(mbus_w - 1 downto 0);
        cbus_out        :   out std_logic_vector(cbus_w - 1 downto 0);
        rsp_in          :   in  std_logic_vector(rbus_w - 1 downto 0);
        rsp_stat_in     :   in  std_logic_vector(sbus_w - 1 downto 0)
    );
end entity main_control;

architecture structural of main_control is
    signal rx_rst       :   std_logic;
    signal rx_fifo_rst  :   std_logic;
    signal rx_idle      :   std_logic;
    signal rx_ren       :   std_logic;
    signal rx_wen       :   std_logic;
    signal rx_empty     :   std_logic;
    signal rx_full      :   std_logic;
    signal rxd          :   std_logic_vector(7 downto 0); -- Data received from receiver and sent to fifo
    signal rx_char      :   std_logic_vector(7 downto 0); -- Data read from fifo and sent to control logic

    signal tx_rst       :   std_logic;
    signal tx_fifo_rst  :   std_logic;
    signal tx_idle      :   std_logic;
    signal tx_ren       :   std_logic;
    signal tx_wen       :   std_logic;
    signal tx_empty     :   std_logic;
    signal tx_full      :   std_logic;
    signal tx_notemp    :   std_logic;
    signal txd          :   std_logic_vector(7 downto 0); -- Data sent to transmitter
    signal tx_char      :   std_logic_vector(7 downto 0); -- Data read from control logic and sent to fifo

    signal cc_rst       :   std_logic;

    -- Instantiating Vivado IPs in this design.
    component fifo_generator_0
        PORT(
            clk : in std_logic;
            srst : in std_logic;
            din : in std_logic_vector(7 downto 0);
            wr_en : in std_logic;
            rd_en : in std_logic;
            dout : out std_logic_vector(7 downto 0);
            full : out std_logic;
            empty : out std_logic;
            wr_rst_busy : out std_logic;
            rd_rst_busy : out std_logic 
        );
    end component;
begin
    uart_rx : entity work.uart_rx port map(
        clk         =>  clk,
        rst         =>  rx_rst,
        rxd_in      =>  rxd_in,
        dout        =>  rxd,
        dval_out    =>  rx_wen,
        idle_out    =>  rx_idle
    );
    rx_rst <= rst;

    -- Vivado IP, 8 bits width, 512 depth
    fifo_rx : fifo_generator_0 port map(
        clk         =>  clk,
        srst        =>  rx_fifo_rst,
        din         =>  rxd,
        wr_en       =>  rx_wen,
        rd_en       =>  rx_ren,
        dout        =>  rx_char,
        full        =>  rx_full,
        empty       =>  rx_empty,
        wr_rst_busy =>  open,
        rd_rst_busy =>  open
    );
    rx_fifo_rst <= rst;

    uart_tx : entity work.uart_tx port map(
        clk         =>  clk,
        rst         =>  tx_rst,
        txd_out     =>  txd_out,
        din         =>  txd,
        dval_in     =>  tx_notemp,
        den_out     =>  tx_ren,
        idle_out    =>  tx_idle
    );
    tx_rst <= rst;
    tx_notemp <= not tx_empty;

    -- Vivado IP, 8 bits width, 512 depth
    fifo_tx : fifo_generator_0 port map(
        clk         =>  clk,
        srst        =>  tx_fifo_rst,
        din         =>  tx_char,
        wr_en       =>  tx_ren,
        rd_en       =>  tx_wen,
        dout        =>  txd,
        full        =>  tx_full,
        empty       =>  tx_empty,
        wr_rst_busy =>  open,
        rd_rst_busy =>  open
    );
    tx_fifo_rst <= rst;

    central_control : entity work.central_control port map(
        clk         =>  clk,
        rst         =>  cc_rst,
        rxd_in      =>  rx_char,
        rxen_out    =>  rx_ren,
        rxemp_in    =>  rx_empty,
        txd_out     =>  tx_char,
        txen_out    =>  tx_wen,
        txful_in    =>  tx_full,
        rsp_in      =>  rsp_in,
        rsp_stat_in =>  rsp_stat_in,
        dbus_out    =>  dbus_out,
        abus_out    =>  abus_out,
        mbus_out    =>  mbus_out,
        cbus_out    =>  cbus_out
    );
    cc_rst <= rst;
end architecture structural;