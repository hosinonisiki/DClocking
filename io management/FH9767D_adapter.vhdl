-- ///////////////Documentation////////////////////
-- Maps several io signals along with spi signals
-- to the universal LPC interface. Contains FIFO logic. 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library xpm;
use xpm.vcomponents.all;

use work.mypak.all;

entity FH9767D_adapter is
    port(
        dac_a_data      :   in  std_logic_vector(15 downto 0);
        dac_b_data      :   in  std_logic_vector(15 downto 0);
        dac_c_data      :   in  std_logic_vector(15 downto 0);
        dac_d_data      :   in  std_logic_vector(15 downto 0);
    
        sys_clk         :   in  std_logic;
        dac_clk_125M    :   in  std_logic;
        sys_rst         :   in  std_logic;

        dac_a_data_fmc  :   out std_logic_vector(13 downto 0);
        dac_b_data_fmc  :   out std_logic_vector(13 downto 0);
        dac_c_data_fmc  :   out std_logic_vector(13 downto 0);
        dac_d_data_fmc  :   out std_logic_vector(13 downto 0);
        dac_a_wrt_fmc   :   out std_logic;
        dac_b_wrt_fmc   :   out std_logic;
        dac_c_wrt_fmc   :   out std_logic;
        dac_d_wrt_fmc   :   out std_logic;
        dac_a_clk_fmc   :   out std_logic;
        dac_b_clk_fmc   :   out std_logic;
        dac_c_clk_fmc   :   out std_logic;
        dac_d_clk_fmc   :   out std_logic
    );
end entity FH9767D_adapter;

architecture structural of FH9767D_adapter is
    signal dac_a_data_buf   : std_logic_vector(13 downto 0);
    signal dac_b_data_buf   : std_logic_vector(13 downto 0);
    signal dac_c_data_buf   : std_logic_vector(13 downto 0);
    signal dac_d_data_buf   : std_logic_vector(13 downto 0);
    signal dac_a_wrt        : std_logic;
    signal dac_b_wrt        : std_logic;
    signal dac_c_wrt        : std_logic;
    signal dac_d_wrt        : std_logic;

    signal dac_a_data_fifo_rrst_busy    : std_logic;
    signal dac_a_data_fifo_wrst_busy    : std_logic;
    signal dac_a_data_fifo_empty        : std_logic;
    signal dac_a_data_fifo_full         : std_logic;
    signal dac_a_data_fifo_ren          : std_logic;
    signal dac_a_data_fifo_wen          : std_logic;
    signal dac_a_data_fifo_wen_1        : std_logic;
    signal dac_b_data_fifo_rrst_busy    : std_logic;
    signal dac_b_data_fifo_wrst_busy    : std_logic;
    signal dac_b_data_fifo_empty        : std_logic;
    signal dac_b_data_fifo_full         : std_logic;
    signal dac_b_data_fifo_ren          : std_logic;
    signal dac_b_data_fifo_wen          : std_logic;
    signal dac_b_data_fifo_wen_1        : std_logic;
    signal dac_c_data_fifo_rrst_busy    : std_logic;
    signal dac_c_data_fifo_wrst_busy    : std_logic;
    signal dac_c_data_fifo_empty        : std_logic;
    signal dac_c_data_fifo_full         : std_logic;
    signal dac_c_data_fifo_ren          : std_logic;
    signal dac_c_data_fifo_wen          : std_logic;
    signal dac_c_data_fifo_wen_1        : std_logic;
    signal dac_d_data_fifo_rrst_busy    : std_logic;
    signal dac_d_data_fifo_wrst_busy    : std_logic;
    signal dac_d_data_fifo_empty        : std_logic;
    signal dac_d_data_fifo_full         : std_logic;
    signal dac_d_data_fifo_ren          : std_logic;
    signal dac_d_data_fifo_wen          : std_logic;
    signal dac_d_data_fifo_wen_1        : std_logic;
begin
    -- AN9767 works at 125MHz, which is half of the system clock
    -- The rising edge of CLK should be earlier than the rising edge of WRT
    -- Use CDC FIFOs to transfer data, and generate dac_wrt signal with ODDREs
    -- in the destination clock domain
    --             ____      _____       _____       _____
    -- sys_clk ___/    \____/     \_____/     \_____/     \___
    --             _________             ___________
    -- dac_clk ___/         \___________/           \_________
    --                       ___________             ___________
    -- dac_wrt _____________/           \___________/           \___

    dac_a_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_clk_125M,
        rst => sys_rst,
        wdata_in => dac_a_data(15 downto 2),
        wen_in => dac_a_data_fifo_wen,
        rdata_out => dac_a_data_buf,
        ren_in => dac_a_data_fifo_ren,
        wrst_busy_out => dac_a_data_fifo_wrst_busy,
        rrst_busy_out => dac_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_a_data_fifo_empty,
        wfull_out => dac_a_data_fifo_full,
        rfull_out => open
    );
    dac_a_data_fifo_wen <= (not dac_a_data_fifo_full and not dac_a_data_fifo_wen_1) and not dac_a_data_fifo_wrst_busy;
    dac_a_data_fifo_ren <= not dac_a_data_fifo_empty and not dac_a_data_fifo_rrst_busy;
    dac_b_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_clk_125M,
        rst => sys_rst,
        wdata_in => dac_b_data(15 downto 2),
        wen_in => dac_b_data_fifo_wen,
        rdata_out => dac_b_data_buf,
        ren_in => dac_b_data_fifo_ren,
        wrst_busy_out => dac_b_data_fifo_wrst_busy,
        rrst_busy_out => dac_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_b_data_fifo_empty,
        wfull_out => dac_b_data_fifo_full,
        rfull_out => open
    );
    dac_b_data_fifo_wen <= (not dac_b_data_fifo_full and not dac_b_data_fifo_wen_1) and not dac_b_data_fifo_wrst_busy;
    dac_b_data_fifo_ren <= not dac_b_data_fifo_empty and not dac_b_data_fifo_rrst_busy;
    dac_c_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_clk_125M,
        rst => sys_rst,
        wdata_in => dac_c_data(15 downto 2),
        wen_in => dac_c_data_fifo_wen,
        rdata_out => dac_c_data_buf,
        ren_in => dac_c_data_fifo_ren,
        wrst_busy_out => dac_c_data_fifo_wrst_busy,
        rrst_busy_out => dac_c_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_c_data_fifo_empty,
        wfull_out => dac_c_data_fifo_full,
        rfull_out => open
    );
    dac_c_data_fifo_wen <= (not dac_c_data_fifo_full and not dac_c_data_fifo_wen_1) and not dac_c_data_fifo_wrst_busy;
    dac_c_data_fifo_ren <= not dac_c_data_fifo_empty and not dac_c_data_fifo_rrst_busy;
    dac_d_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_clk_125M,
        rst => sys_rst,
        wdata_in => dac_d_data(15 downto 2),
        wen_in => dac_d_data_fifo_wen,
        rdata_out => dac_d_data_buf,
        ren_in => dac_d_data_fifo_ren,
        wrst_busy_out => dac_d_data_fifo_wrst_busy,
        rrst_busy_out => dac_d_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_d_data_fifo_empty,
        wfull_out => dac_d_data_fifo_full,
        rfull_out => open
    );
    dac_d_data_fifo_wen <= (not dac_d_data_fifo_full and not dac_d_data_fifo_wen_1) and not dac_d_data_fifo_wrst_busy;
    dac_d_data_fifo_ren <= not dac_d_data_fifo_empty and not dac_d_data_fifo_rrst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            dac_a_data_fifo_wen_1 <= dac_a_data_fifo_wen;
            dac_b_data_fifo_wen_1 <= dac_b_data_fifo_wen;
            dac_c_data_fifo_wen_1 <= dac_c_data_fifo_wen;
            dac_d_data_fifo_wen_1 <= dac_d_data_fifo_wen;
        end if;
    end process;

    -- ODDREs
    dac_a_wrt_oddre1 : ODDRE1 port map(
        D1 => std_logic'('0'),
        D2 => std_logic'('1'),
        C => dac_clk_125M,
        Q => dac_a_wrt,
        SR => sys_rst
    );
    dac_b_wrt_oddre1 : ODDRE1 port map(
        D1 => std_logic'('0'),
        D2 => std_logic'('1'),
        C => dac_clk_125M,
        Q => dac_b_wrt,
        SR => sys_rst
    );
    dac_c_wrt_oddre1 : ODDRE1 port map(
        D1 => std_logic'('0'),
        D2 => std_logic'('1'),
        C => dac_clk_125M,
        Q => dac_c_wrt,
        SR => sys_rst
    );
    dac_d_wrt_oddre1 : ODDRE1 port map(
        D1 => std_logic'('0'),
        D2 => std_logic'('1'),
        C => dac_clk_125M,
        Q => dac_d_wrt,
        SR => sys_rst
    );

    dac_a_data_fmc(13) <= not dac_a_data_buf(13);
    dac_a_data_fmc(12 downto 0) <= dac_a_data_buf(12 downto 0);
    dac_b_data_fmc(13) <= not dac_b_data_buf(13);
    dac_b_data_fmc(12 downto 0) <= dac_b_data_buf(12 downto 0);
    dac_c_data_fmc(13) <= not dac_c_data_buf(13);
    dac_c_data_fmc(12 downto 0) <= dac_c_data_buf(12 downto 0);
    dac_d_data_fmc(13) <= not dac_d_data_buf(13);
    dac_d_data_fmc(12 downto 0) <= dac_d_data_buf(12 downto 0);
    dac_a_wrt_fmc <= dac_a_wrt;
    dac_b_wrt_fmc <= dac_b_wrt;
    dac_c_wrt_fmc <= dac_c_wrt;
    dac_d_wrt_fmc <= dac_d_wrt;
    dac_a_clk_fmc <= dac_clk_125M;
    dac_b_clk_fmc <= dac_clk_125M;
    dac_c_clk_fmc <= dac_clk_125M;
    dac_d_clk_fmc <= dac_clk_125M;
end architecture structural;
