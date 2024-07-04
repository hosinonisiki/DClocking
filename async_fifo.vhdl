-- ///////////////Documentation////////////////////
-- Asynchronous FIFO used to deliver data from slow
-- system clock to fast dac clock. It is assumed that
-- fast clock is fast enough so that fifo will never
-- be full. Encapsulates the xpm_fifo_async module
-- from Xilinx.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

library xpm;
use xpm.vcomponents.all;

entity async_fifo is
    generic(
        width : integer;
        depth : integer := 2048
    );
    port(
        wclk            :   in  std_logic; -- write clock
        rclk            :   in  std_logic; -- read clock
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(width - 1 downto 0);
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(width - 1 downto 0);
        ren_in          :   in std_logic;
        rval_out        :   out std_logic;
        rst_busy_out    :   out std_logic;
        empty_out       :   out std_logic
    );
end entity async_fifo;

architecture structural of async_fifo is
    signal rd_rst_busy : std_logic;
    signal wr_rst_busy : std_logic;
begin
    async_fifo_inst : xpm_fifo_async generic map(
        CASCADE_HEIGHT => 0,        -- DECIMAL
        CDC_SYNC_STAGES => 2,       -- DECIMAL
        DOUT_RESET_VALUE => "0",    -- String
        ECC_MODE => "no_ecc",       -- String
        FIFO_MEMORY_TYPE => "auto", -- String
        FIFO_READ_LATENCY => 1,     -- DECIMAL
        FIFO_WRITE_DEPTH => depth,   -- DECIMAL
        FULL_RESET_VALUE => 0,      -- DECIMAL
        PROG_EMPTY_THRESH => 10,    -- DECIMAL
        PROG_FULL_THRESH => 10,     -- DECIMAL
        RD_DATA_COUNT_WIDTH => 1,   -- DECIMAL
        READ_DATA_WIDTH => width,      -- DECIMAL
        READ_MODE => "std",         -- String
        RELATED_CLOCKS => 0,        -- DECIMAL
        SIM_ASSERT_CHK => 0,        -- DECIMAL; 0=disable simulation messages, 1=enable simulation messages
        USE_ADV_FEATURES => "0707", -- String
        WAKEUP_TIME => 0,           -- DECIMAL
        WRITE_DATA_WIDTH => width,     -- DECIMAL
        WR_DATA_COUNT_WIDTH => 1    -- DECIMAL
   )port map(
        almost_empty => open,
        almost_full => open,
        data_valid => rval_out,
        dbiterr => open,
        dout => rdata_out,
        empty => open,
        full => open,
        overflow => open,
        prog_empty => empty_out,
        prog_full => open,
        rd_data_count => open,
        rd_rst_busy => rd_rst_busy,
        sbiterr => open,
        underflow => open,
        wr_ack => open,
        wr_data_count => open,
        wr_rst_busy => wr_rst_busy,
        din => wdata_in,
        injectdbiterr => '0',
        injectsbiterr => '0',
        rd_clk => rclk,
        rd_en => ren_in,
        rst => rst,
        sleep => '0',
        wr_clk => wclk,
        wr_en => wen_in
   );

   rst_busy_out <= rd_rst_busy or wr_rst_busy;
end architecture structural;