-- ///////////////Documentation////////////////////
-- This design is the main control unit of the system.
-- It involves an entity containing control logic,
-- a uart receiver and a transmitter, along with
-- two fifo buffers.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

-- Instantiating Vivado IPs in this design.
library unisim;
use unisim.vcomponents.all;

library unimacro;
use unimacro.vcomponents.all;

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
        rsp_stat_in     :   in  std_logic_vector(sbus_w downto 0)
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

    -- Vivado Macro
    fifo_rx : FIFO_SYNC_MACRO generic map(
        data_width      =>  8,
        fifo_size       =>  "18Kb" -- Max data velocity on a uart bus is far slower than the velocity at which central control unit can process data.
                                   -- Therefore, the size of receiver fifo can be kept small.
                                   -- Notice that this design does not detect if the receiver fifo is full, which can lead to data loss in very rare cases.
        -- other generics set as default    
    )port map(
        almostempty     =>  open,
        almostfull      =>  open,
        do              =>  rx_char,
        empty           =>  rx_empty,
        full            =>  rx_full,
        rdcount         =>  open,
        rderr           =>  open, -- This design does not handle internal errors in the fifo.
        wrcount         =>  open,
        wrerr           =>  open,
        clk             =>  clk,
        di              =>  rxd,
        rden            =>  rx_ren,
        rst             =>  rx_fifo_rst,
        wren            =>  rx_wen
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

    -- Vivado Macro
    fifo_tx : FIFO_SYNC_MACRO generic map(
        data_width      =>  8,
        fifo_size       =>  "36Kb" -- The size of the transmitter fifo is kept larger than the receiver fifo to prevent data loss.
        -- other generics set as default
    )port map(
        almostempty     =>  open,
        almostfull      =>  open,
        do              =>  txd,
        empty           =>  tx_empty,
        full            =>  tx_full,
        rdcount         =>  open,
        rderr           =>  open, -- This design does not handle internal errors in the fifo.
        wrcount         =>  open,
        wrerr           =>  open,
        clk             =>  clk,
        di              =>  tx_char,
        rden            =>  tx_ren,
        rst             =>  tx_fifo_rst,
        wren            =>  tx_wen
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