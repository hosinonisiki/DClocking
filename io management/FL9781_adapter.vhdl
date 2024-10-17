-- ///////////////Documentation////////////////////
-- Maps several output signals along with spi signals
-- to the universal LPC interface. Contains FIFO logic. 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Instantiating Kintex Ultrascale primitives
library unisim;
use unisim.vcomponents.all;

use work.mypak.all;

entity FL9781_adapter is
    port(
        dac_a_data      :   in  std_logic_vector(13 downto 0);
        dac_b_data      :   in  std_logic_vector(13 downto 0);
        dac_c_data      :   in  std_logic_vector(13 downto 0);
        dac_d_data      :   in  std_logic_vector(13 downto 0);
        dac_a_b_spi_ss  :   in  std_logic;
        dac_c_d_spi_ss  :   in  std_logic;
        dac_clk_spi_ss  :   in  std_logic;
        dac_spi_sck     :   in  std_logic;
        dac_spi_mosi    :   in  std_logic;
        dac_spi_miso    :   out std_logic;
        sys_clk         :   in  std_logic;
        sys_rst         :   in  std_logic;

        dac_a_b_data_fmc : out std_logic_vector(13 downto 0);
        dac_c_d_data_fmc : out std_logic_vector(13 downto 0);
        dac_a_b_dco_fmc : in std_logic;
        dac_c_d_dco_fmc : in std_logic;
        dac_a_b_dci_fmc : out std_logic;
        dac_c_d_dci_fmc : out std_logic;
        dac_a_b_spi_ss_fmc : out std_logic;
        dac_c_d_spi_ss_fmc : out std_logic;
        dac_clk_spi_ss_fmc : out std_logic;
        dac_spi_sck_fmc : out std_logic;
        dac_spi_mosi_fmc : out std_logic;
        dac_spi_miso_fmc : in std_logic;
        dac_eeprom_iic_scl_fmc : out std_logic;
        dac_eeprom_iic_sda_fmc : out std_logic
    );
end entity FL9781_adapter;

architecture structural of FL9781_adapter is
    signal sys_rst_bar       :   std_logic;

    signal dac_a_b_data_h_buf : std_logic_vector(13 downto 0);
    signal dac_a_b_data_l_buf : std_logic_vector(13 downto 0);
    signal dac_c_d_data_h_buf : std_logic_vector(13 downto 0);
    signal dac_c_d_data_l_buf : std_logic_vector(13 downto 0);
    signal dac_a_b_data_h : std_logic_vector(13 downto 0);
    signal dac_a_b_data_l : std_logic_vector(13 downto 0);
    signal dac_c_d_data_h : std_logic_vector(13 downto 0);
    signal dac_c_d_data_l : std_logic_vector(13 downto 0);
    signal dac_a_b_data : std_logic_vector(13 downto 0);
    signal dac_c_d_data : std_logic_vector(13 downto 0);
    signal dac_a_b_dci_h : std_logic;
    signal dac_a_b_dci_l : std_logic;
    signal dac_c_d_dci_h : std_logic;
    signal dac_c_d_dci_l : std_logic;
    signal dac_a_b_dci : std_logic;
    signal dac_c_d_dci : std_logic;
    signal dac_a_b_dco : std_logic;
    signal dac_c_d_dco : std_logic;
    signal dac_eeprom_iic_scl : std_logic;
    signal dac_eeprom_iic_sda : std_logic;

    signal dac_a_data_fifo_wrst_busy : std_logic;
    signal dac_a_data_fifo_rrst_busy : std_logic;
    signal dac_a_data_fifo_empty : std_logic;
    signal dac_a_data_fifo_full : std_logic;
    signal dac_a_data_fifo_ren : std_logic;
    signal dac_a_data_fifo_ren_1 : std_logic;
    signal dac_b_data_fifo_wrst_busy : std_logic;
    signal dac_b_data_fifo_rrst_busy : std_logic;
    signal dac_b_data_fifo_empty : std_logic;
    signal dac_b_data_fifo_full : std_logic;
    signal dac_b_data_fifo_ren : std_logic;
    signal dac_b_data_fifo_ren_1 : std_logic;
    signal dac_c_data_fifo_wrst_busy : std_logic;
    signal dac_c_data_fifo_rrst_busy : std_logic;
    signal dac_c_data_fifo_empty : std_logic;
    signal dac_c_data_fifo_full : std_logic;
    signal dac_c_data_fifo_ren : std_logic;
    signal dac_c_data_fifo_ren_1 : std_logic;
    signal dac_d_data_fifo_wrst_busy : std_logic;
    signal dac_d_data_fifo_rrst_busy : std_logic;
    signal dac_d_data_fifo_empty : std_logic;
    signal dac_d_data_fifo_full : std_logic;
    signal dac_d_data_fifo_ren : std_logic;
    signal dac_d_data_fifo_ren_1 : std_logic;
begin
    -- Interface
    -- Align data transferred with lvds data clock
    -- Transfer data from slow system clock to fast dac clock by employing asynchronous fifo
    -- Read latency is known to be 1 cycle, so don't care valid signal
    dac_a_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_a_b_dco,
        rst => sys_rst_bar,
        wdata_in => dac_a_data,
        wen_in => not dac_a_data_fifo_wrst_busy,
        rdata_out => dac_a_b_data_h_buf,
        ren_in => dac_a_data_fifo_ren,
        wrst_busy_out => dac_a_data_fifo_wrst_busy,
        rrst_busy_out => dac_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_a_data_fifo_empty,
        wfull_out => open,
        rfull_out => dac_a_data_fifo_full
    );
    -- Period ratio is approximately 1:2, which means 1 input is read every 2 cycles on average, but there can be exceptions
    -- The following logic is employed to adjust data rate on the fly, by whether delaying or advancing the read by 1 cycle
    -- The above comments are out of date.
    -- The period ratio has been changed to 1:4, but since this module is currently not instantiated,
    -- the modifications will be made later.
    dac_a_data_fifo_ren <= ((not dac_a_data_fifo_empty and not dac_a_data_fifo_ren_1) or dac_a_data_fifo_full) and not dac_a_data_fifo_rrst_busy;
    dac_b_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_a_b_dco,
        rst => sys_rst_bar,
        wdata_in => dac_b_data,
        wen_in => not dac_b_data_fifo_wrst_busy,
        rdata_out => dac_a_b_data_l_buf,
        ren_in => dac_b_data_fifo_ren,
        wrst_busy_out => dac_b_data_fifo_wrst_busy,
        rrst_busy_out => dac_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_b_data_fifo_empty,
        wfull_out => open,
        rfull_out => dac_b_data_fifo_full
    );
    dac_b_data_fifo_ren <= ((not dac_b_data_fifo_empty and not dac_b_data_fifo_ren_1) or dac_b_data_fifo_full) and not dac_b_data_fifo_rrst_busy;
    process(dac_a_b_dco)
    begin
        if rising_edge(dac_a_b_dco) then
            dac_a_data_fifo_ren_1 <= dac_a_data_fifo_ren;
            dac_b_data_fifo_ren_1 <= dac_b_data_fifo_ren;
            if dac_a_data_fifo_ren_1 = '1' then
                dac_a_b_data_h <= dac_a_b_data_h_buf;
            end if;
            if dac_b_data_fifo_ren_1 = '1' then
                dac_a_b_data_l <= dac_a_b_data_l_buf;
            end if;
        end if;
    end process;
    dac_c_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_c_d_dco,
        rst => sys_rst_bar,
        wdata_in => dac_c_data,
        wen_in => not dac_c_data_fifo_wrst_busy,
        rdata_out => dac_c_d_data_h_buf,
        ren_in => dac_c_data_fifo_ren,
        wrst_busy_out => dac_c_data_fifo_wrst_busy,
        rrst_busy_out => dac_c_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => dac_c_data_fifo_empty,
        wfull_out => open,
        rfull_out => dac_c_data_fifo_full
    );
    dac_c_data_fifo_ren <= ((not dac_c_data_fifo_empty and not dac_c_data_fifo_ren_1) or dac_c_data_fifo_full) and not dac_c_data_fifo_rrst_busy;
    dac_d_data_fifo : entity work.async_fifo generic map(
        width => 14
    )port map(
        wclk => sys_clk,
        rclk => dac_c_d_dco,
        rst => sys_rst_bar,
        wdata_in => dac_d_data,
        wen_in => not dac_d_data_fifo_wrst_busy,
        rdata_out => dac_c_d_data_l_buf,
        ren_in => dac_d_data_fifo_ren,
        wrst_busy_out => dac_d_data_fifo_wrst_busy,
        wempty_out => open,
        rempty_out => dac_d_data_fifo_empty,
        wfull_out => open,
        rfull_out => dac_d_data_fifo_full
    );
    dac_d_data_fifo_ren <= ((not dac_d_data_fifo_empty and not dac_d_data_fifo_ren_1) or dac_d_data_fifo_full) and not dac_d_data_fifo_rrst_busy;
    process(dac_c_d_dco)
    begin
        if rising_edge(dac_c_d_dco) then
            dac_c_data_fifo_ren_1 <= dac_c_data_fifo_ren;
            dac_d_data_fifo_ren_1 <= dac_d_data_fifo_ren;
            if dac_c_data_fifo_ren_1 = '1' then
                dac_c_d_data_h <= dac_c_d_data_h_buf;
            end if;
            if dac_d_data_fifo_ren_1 = '1' then
                dac_c_d_data_l <= dac_c_d_data_l_buf;
            end if;
        end if;
    end process;

    dac_a_b_dci_h <= '1';
    dac_a_b_dci_l <= '0';
    dac_c_d_dci_h <= '1';
    dac_c_d_dci_l <= '0';
    dac_eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    dac_eeprom_iic_sda <= '0'; -- EEPROM part not finished yet

    -- ODDREs
    dac_a_b_dci_oddre1 : ODDRE1 port map(
        Q => dac_a_b_dci,
        C => dac_a_b_dco,
        D1 => dac_a_b_dci_h,
        D2 => dac_a_b_dci_l,
        SR => sys_rst_bar
    );
    dac_a_b_data_oddre1_gen : for i in 0 to 13 generate
        dac_a_b_data_oddre1 : ODDRE1 port map(
            Q => dac_a_b_data(i),
            C => dac_a_b_dco,
            D1 => dac_a_b_data_h(i),
            D2 => dac_a_b_data_l(i),
            SR => sys_rst_bar
        );
    end generate dac_a_b_data_oddre1_gen;
    dac_c_d_dci_oddre1 : ODDRE1 port map(
        Q => dac_c_d_dci,
        C => dac_c_d_dco,
        D1 => dac_c_d_dci_h,
        D2 => dac_c_d_dci_l,
        SR => sys_rst_bar
    );
    dac_c_d_data_oddre1_gen : for i in 0 to 13 generate
        dac_c_d_data_oddre1 : ODDRE1 port map(
            Q => dac_c_d_data(i),
            C => dac_c_d_dco,
            D1 => dac_c_d_data_h(i),
            D2 => dac_c_d_data_l(i),
            SR => sys_rst_bar
        );
    end generate dac_c_d_data_oddre1_gen;

    dac_a_b_data_fmc <= dac_a_b_data;
    dac_c_d_data_fmc <= dac_c_d_data;
    dac_a_b_dci_fmc <= dac_a_b_dci;
    dac_c_d_dci_fmc <= dac_c_d_dci;
    dac_a_b_dco <= dac_a_b_dco_fmc;
    dac_c_d_dco <= dac_c_d_dco_fmc;
    dac_a_b_spi_ss_fmc <= dac_a_b_spi_ss;
    dac_c_d_spi_ss_fmc <= dac_c_d_spi_ss;
    dac_clk_spi_ss_fmc <= dac_clk_spi_ss;
    dac_spi_sck_fmc <= dac_spi_sck;
    dac_spi_mosi_fmc <= dac_spi_mosi;
    dac_spi_miso <= dac_spi_miso_fmc;
    dac_eeprom_iic_scl_fmc <= dac_eeprom_iic_scl;
    dac_eeprom_iic_sda_fmc <= dac_eeprom_iic_sda;

    -- Misc
    sys_rst_bar <= not sys_rst;
end architecture structural;