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
        wrst_busy_out   :   out std_logic;
        rrst_busy_out   :   out std_logic;
        wempty_out      :   out std_logic;
        rempty_out      :   out std_logic;
        wfull_out       :   out std_logic;
        rfull_out       :   out std_logic
    );
end entity async_fifo;

architecture structural of async_fifo is
    signal empty : std_logic;
    signal empty_1 : std_logic;
    signal empty_2 : std_logic;
    signal full : std_logic;
    signal full_1 : std_logic;
    signal full_2 : std_logic;

    attribute ASYNC_REG : string;
    attribute ASYNC_REG of empty_1 : signal is "TRUE";
    attribute ASYNC_REG of empty_2 : signal is "TRUE";
    attribute ASYNC_REG of full_1 : signal is "TRUE";
    attribute ASYNC_REG of full_2 : signal is "TRUE";
begin
    async_fifo_inst : xpm_fifo_async generic map(
        CASCADE_HEIGHT => 0,        -- DECIMAL
        CDC_SYNC_STAGES => 3,       -- DECIMAL
        DOUT_RESET_VALUE => "0",    -- String
        ECC_MODE => "no_ecc",       -- String
        FIFO_MEMORY_TYPE => "distributed", -- String
        FIFO_READ_LATENCY => 1,     -- DECIMAL
        FIFO_WRITE_DEPTH => depth,   -- DECIMAL
        FULL_RESET_VALUE => 0,      -- DECIMAL
        PROG_EMPTY_THRESH => 20,    -- DECIMAL
        PROG_FULL_THRESH => depth - 20,     -- DECIMAL
        RD_DATA_COUNT_WIDTH => 1,   -- DECIMAL
        READ_DATA_WIDTH => width,      -- DECIMAL
        READ_MODE => "std",         -- String
        RELATED_CLOCKS => 0,        -- DECIMAL
        SIM_ASSERT_CHK => 0,        -- DECIMAL; 0=disable simulation messages, 1=enable simulation messages
        USE_ADV_FEATURES => "0202", -- String
        WAKEUP_TIME => 0,           -- DECIMAL
        WRITE_DATA_WIDTH => width,     -- DECIMAL
        WR_DATA_COUNT_WIDTH => 1    -- DECIMAL
   )port map(
        almost_empty => open,
        almost_full => open,
        data_valid => open,
        dbiterr => open,
        dout => rdata_out,
        empty => open,
        full => open,
        overflow => open,
        prog_empty => empty,
        prog_full => full,
        rd_data_count => open,
        rd_rst_busy => rrst_busy_out,
        sbiterr => open,
        underflow => open,
        wr_ack => open,
        wr_data_count => open,
        wr_rst_busy => wrst_busy_out,
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

    -- empty is on rd_clk domain by default
    rempty_out <= empty;
    process(wclk)
    begin
        if rising_edge(wclk) then
            empty_1 <= empty;
            empty_2 <= empty_1;
        end if;
    end process;
    wempty_out <= empty_2;

    -- full is on wr_clk domain by default
    wfull_out <= full;
    process(rclk)
    begin
        if rising_edge(rclk) then
            full_1 <= full;
            full_2 <= full_1;
        end if;
    end process;
    rfull_out <= full_2;
end architecture structural;