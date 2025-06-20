-- ///////////////Documentation////////////////////
-- Maps input data, output clock and spi signals
-- to the universal LPC interface. Contains FIFO logic. 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Instantiating Kintex Ultrascale primitives
library unisim;
use unisim.vcomponents.all;

use work.mypak.all;

entity FL9627_adapter is
    port(
        adc_a_data      :   out std_logic_vector(11 downto 0);
        adc_b_data      :   out std_logic_vector(11 downto 0);
        adc_c_data      :   out std_logic_vector(11 downto 0);
        adc_d_data      :   out std_logic_vector(11 downto 0);
        adc_a_b_spi_ss  :   in  std_logic;
        adc_c_d_spi_ss  :   in  std_logic;
        adc_spi_sck     :   in  std_logic;
        adc_spi_mosi    :   in  std_logic;
        adc1_spi_miso   :   out std_logic;
        adc2_spi_miso   :   out std_logic;
        adc_spi_io_tri  :   in  std_logic;
        sys_clk         :   in  std_logic;
        adc_clk_125M    :   in  std_logic;
        sys_rst         :   in  std_logic;

        adc_a_b_data_fmc : in std_logic_vector(11 downto 0);
        adc_c_d_data_fmc : in std_logic_vector(11 downto 0);
        adc_a_b_dco_fmc : in std_logic;
        adc_c_d_dco_fmc : in std_logic;
        adc_a_b_spi_ss_fmc : out std_logic;
        adc_c_d_spi_ss_fmc : out std_logic;
        adc_spi_sck_fmc : out std_logic;
        adc_spi_mosi_fmc : out std_logic;
        adc1_spi_miso_fmc : in std_logic;
        adc2_spi_miso_fmc : in std_logic;
        adc_spi_io_tri_fmc : out std_logic;
        adc_clk_125M_fmc : out std_logic;
        adc_eeprom_iic_scl_fmc : out std_logic;
        adc_eeprom_iic_sda_fmc : out std_logic
    );
end entity FL9627_adapter;

architecture structural of FL9627_adapter is
    signal adc_a_data_buf : std_logic_vector(11 downto 0);
    signal adc_b_data_buf : std_logic_vector(11 downto 0);
    signal adc_c_data_buf : std_logic_vector(11 downto 0);
    signal adc_d_data_buf : std_logic_vector(11 downto 0);
    signal adc_a_b_data_h : std_logic_vector(11 downto 0);
    signal adc_a_b_data_l : std_logic_vector(11 downto 0);
    signal adc_c_d_data_h : std_logic_vector(11 downto 0);
    signal adc_c_d_data_l : std_logic_vector(11 downto 0);
    signal adc_a_b_data : std_logic_vector(11 downto 0);
    signal adc_c_d_data : std_logic_vector(11 downto 0);
    signal adc_a_b_dco : std_logic;
    signal adc_c_d_dco : std_logic;
    signal adc_eeprom_iic_scl : std_logic;
    signal adc_eeprom_iic_sda : std_logic;

    signal adc_a_data_fifo_rrst_busy : std_logic;
    signal adc_a_data_fifo_wrst_busy : std_logic;
    signal adc_a_data_fifo_empty : std_logic;
    signal adc_a_data_fifo_full : std_logic;
    signal adc_a_data_fifo_ren : std_logic;
    signal adc_a_data_fifo_ren_1 : std_logic;
    signal adc_b_data_fifo_rrst_busy : std_logic;
    signal adc_b_data_fifo_wrst_busy : std_logic;
    signal adc_b_data_fifo_empty : std_logic;
    signal adc_b_data_fifo_full : std_logic;
    signal adc_b_data_fifo_ren : std_logic;
    signal adc_b_data_fifo_ren_1 : std_logic;
    signal adc_c_data_fifo_rrst_busy : std_logic;
    signal adc_c_data_fifo_wrst_busy : std_logic;
    signal adc_c_data_fifo_empty : std_logic;
    signal adc_c_data_fifo_full : std_logic;
    signal adc_c_data_fifo_ren : std_logic;
    signal adc_c_data_fifo_ren_1 : std_logic;
    signal adc_d_data_fifo_rrst_busy : std_logic;
    signal adc_d_data_fifo_wrst_busy : std_logic;
    signal adc_d_data_fifo_empty : std_logic;
    signal adc_d_data_fifo_full : std_logic;
    signal adc_d_data_fifo_ren : std_logic;
    signal adc_d_data_fifo_ren_1 : std_logic;
begin
    -- Interface
    -- Transfer data from slow adc clock to system clock by employing asynchronous fifo
    adc_a_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_a_b_dco,
        rclk => sys_clk,
        rst => sys_rst,
        wdata_in => adc_a_b_data_h,
        wen_in => not adc_a_data_fifo_wrst_busy,
        rdata_out => adc_a_data_buf,
        ren_in => adc_a_data_fifo_ren,
        wrst_busy_out => adc_a_data_fifo_wrst_busy,
        rrst_busy_out => adc_a_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_a_data_fifo_empty,
        wfull_out => open,
        rfull_out => adc_a_data_fifo_full
    );
    adc_a_data_fifo_ren <= ((not adc_a_data_fifo_empty and not adc_a_data_fifo_ren_1) or adc_a_data_fifo_full) and not adc_a_data_fifo_rrst_busy;
    adc_b_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_a_b_dco,
        rclk => sys_clk,
        rst => sys_rst,
        wdata_in => adc_a_b_data_l,
        wen_in => not adc_b_data_fifo_wrst_busy,
        rdata_out => adc_b_data_buf,
        ren_in => adc_b_data_fifo_ren,
        wrst_busy_out => adc_b_data_fifo_wrst_busy,
        rrst_busy_out => adc_b_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_b_data_fifo_empty,
        wfull_out => open,
        rfull_out => adc_b_data_fifo_full
    );
    adc_b_data_fifo_ren <= ((not adc_b_data_fifo_empty and not adc_b_data_fifo_ren_1) or adc_b_data_fifo_full) and not adc_b_data_fifo_rrst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            adc_a_data_fifo_ren_1 <= adc_a_data_fifo_ren;
            adc_b_data_fifo_ren_1 <= adc_b_data_fifo_ren;
            if adc_a_data_fifo_ren_1 = '1' then
                -- By default, FL9627 uses 1000 for MAX, 0000 for 0 and 0111 for MIN in 2's complement mode (set by command)
                -- Reverse all bits of the data, same applies to b, c and d
                adc_a_data <= not adc_a_data_buf;
            end if;
            if adc_b_data_fifo_ren_1 = '1' then
                adc_b_data <= not adc_b_data_buf;
            end if;
        end if;
    end process;
    adc_c_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_c_d_dco,
        rclk => sys_clk,
        rst => sys_rst,
        wdata_in => adc_c_d_data_h,
        wen_in => not adc_c_data_fifo_wrst_busy,
        rdata_out => adc_c_data_buf,
        ren_in => adc_c_data_fifo_ren,
        wrst_busy_out => adc_c_data_fifo_wrst_busy,
        rrst_busy_out => adc_c_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_c_data_fifo_empty,
        wfull_out => open,
        rfull_out => adc_c_data_fifo_full
    );
    adc_c_data_fifo_ren <= ((not adc_c_data_fifo_empty and not adc_c_data_fifo_ren_1) or adc_c_data_fifo_full) and not adc_c_data_fifo_rrst_busy;
    adc_d_data_fifo : entity work.async_fifo generic map(
        width => 12
    )port map(
        wclk => adc_c_d_dco,
        rclk => sys_clk,
        rst => sys_rst,
        wdata_in => adc_c_d_data_l,
        wen_in => not adc_d_data_fifo_wrst_busy,
        rdata_out => adc_d_data_buf,
        ren_in => adc_d_data_fifo_ren,
        wrst_busy_out => adc_d_data_fifo_wrst_busy,
        rrst_busy_out => adc_d_data_fifo_rrst_busy,
        wempty_out => open,
        rempty_out => adc_d_data_fifo_empty,
        wfull_out => open,
        rfull_out => adc_d_data_fifo_full
    );
    adc_d_data_fifo_ren <= ((not adc_d_data_fifo_empty and not adc_d_data_fifo_ren_1) or adc_d_data_fifo_full) and not adc_d_data_fifo_rrst_busy;
    process(sys_clk)
    begin
        if rising_edge(sys_clk) then
            adc_c_data_fifo_ren_1 <= adc_c_data_fifo_ren;
            adc_d_data_fifo_ren_1 <= adc_d_data_fifo_ren;
            if adc_c_data_fifo_ren_1 = '1' then
                adc_c_data <= not adc_c_data_buf;
            end if;
            if adc_d_data_fifo_ren_1 = '1' then
                adc_d_data <= not adc_d_data_buf;
            end if;
        end if;
    end process;

    adc_eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    adc_eeprom_iic_sda <= '0'; -- EEPROM part not finished yet

    -- IDDREs
    adc_a_b_data_iddre1_gen : for i in 0 to 11 generate
        adc_a_b_data_iddre1 : IDDRE1 port map(
            Q1 => adc_a_b_data_h(i),
            Q2 => adc_a_b_data_l(i),
            C => adc_a_b_dco,
            CB => not adc_a_b_dco,
            D => adc_a_b_data(i),
            R => sys_rst
        );
    end generate adc_a_b_data_iddre1_gen;
    adc_c_d_data_iddre1_gen : for i in 0 to 11 generate
        adc_c_d_data_iddre1 : IDDRE1 port map(
            Q1 => adc_c_d_data_h(i),
            Q2 => adc_c_d_data_l(i),
            C => adc_c_d_dco,
            CB => not adc_c_d_dco,
            D => adc_c_d_data(i),
            R => sys_rst
        );
    end generate adc_c_d_data_iddre1_gen;

    adc_a_b_data <= adc_a_b_data_fmc;
    adc_c_d_data <= adc_c_d_data_fmc;
    adc_a_b_dco <= adc_a_b_dco_fmc;
    adc_c_d_dco <= adc_c_d_dco_fmc;
    adc_a_b_spi_ss_fmc <= adc_a_b_spi_ss;
    adc_c_d_spi_ss_fmc <= adc_c_d_spi_ss;
    adc_spi_sck_fmc <= adc_spi_sck;
    adc_spi_mosi_fmc <= adc_spi_mosi;
    adc1_spi_miso <= adc1_spi_miso_fmc;
    adc2_spi_miso <= adc2_spi_miso_fmc;
    adc_spi_io_tri_fmc <= adc_spi_io_tri;
    adc_clk_125M_fmc <= adc_clk_125M;
    adc_eeprom_iic_scl_fmc <= adc_eeprom_iic_scl;
    adc_eeprom_iic_sda_fmc <= adc_eeprom_iic_sda;
end architecture structural;
        
