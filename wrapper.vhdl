-- ///////////////Documentation////////////////////
-- Adapt the io ports to fit the hardware.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Instantiating Kintex Ultrascale primitives
library unisim;
use unisim.vcomponents.all;

use work.mypak.all;

entity wrapper is
    port(
        sys_clk_p       :   in  std_logic;
        sys_clk_n       :   in  std_logic;
        rst             :   in  std_logic;

        -- LED lights
        led_1_o         :   out std_logic;
        led_2_o         :   out std_logic;
        led_3_o         :   out std_logic;
        led_4_o         :   out std_logic;
        panel_led_1_o   :   out std_logic;
        panel_led_2_o   :   out std_logic;

        -- To serial port
        uart_txd_o      :   out std_logic;
        uart_rxd_i      :   in  std_logic;

        -- To FL9781
        dac_1_2_dci_p_ddr_o     :   out std_logic;
        dac_1_2_dci_n_ddr_o     :   out std_logic;
        dac_1_2_dco_p_i         :   in  std_logic;
        dac_1_2_dco_n_i         :   in  std_logic;
        dac_1_2_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_1_2_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_1_2_spi_ss_o        :   out std_logic;
        dac_3_4_dci_p_ddr_o     :   out std_logic;
        dac_3_4_dci_n_ddr_o     :   out std_logic;
        dac_3_4_dco_p_i         :   in  std_logic;
        dac_3_4_dco_n_i         :   in  std_logic;
        dac_3_4_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_3_4_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_3_4_spi_ss_o        :   out std_logic;
        dac_clk_spi_ss_o        :   out std_logic;
        dac_spi_sck_o           :   out std_logic;
        dac_spi_mosi_o          :   out std_logic;
        dac_spi_miso_i          :   in  std_logic;
        dac_eeprom_iic_scl_o    :   out std_logic;
        dac_eeprom_iic_sda_io   :   inout std_logic
    );
end entity wrapper;

architecture peripheral_wrapper of wrapper is
    signal sys_clk : std_logic;
    signal sys_rst : std_logic;
    signal sys_rst_bar : std_logic;

    signal led_1 : std_logic;
    signal led_2 : std_logic;
    signal led_3 : std_logic;
    signal led_4 : std_logic;
    signal panel_led_1 : std_logic;
    signal panel_led_2 : std_logic;

    signal uart_txd : std_logic;
    signal uart_rxd : std_logic;
    signal dac_1_2_data_p_h : std_logic_vector(13 downto 0);
    signal dac_1_2_data_p_l : std_logic_vector(13 downto 0);
    signal dac_1_2_data_n_h : std_logic_vector(13 downto 0);
    signal dac_1_2_data_n_l : std_logic_vector(13 downto 0);
    signal dac_3_4_data_p_h : std_logic_vector(13 downto 0);
    signal dac_3_4_data_p_l : std_logic_vector(13 downto 0);
    signal dac_3_4_data_n_h : std_logic_vector(13 downto 0);
    signal dac_3_4_data_n_l : std_logic_vector(13 downto 0);
    signal dac_1_2_dci_p_h : std_logic;
    signal dac_1_2_dci_p_l : std_logic;
    signal dac_1_2_dci_n_h : std_logic;
    signal dac_1_2_dci_n_l : std_logic;
    signal dac_3_4_dci_p_h : std_logic;
    signal dac_3_4_dci_p_l : std_logic;
    signal dac_3_4_dci_n_h : std_logic;
    signal dac_3_4_dci_n_l : std_logic;
    signal dac_1_2_dco : std_logic;
    signal dac_3_4_dco : std_logic;
    signal dac_1_2_spi_ss : std_logic;
    signal dac_3_4_spi_ss : std_logic;
    signal dac_clk_spi_ss : std_logic;
    signal dac_spi_sck : std_logic;
    signal dac_spi_mosi : std_logic;
    signal dac_spi_miso : std_logic;
    signal dac_eeprom_iic_scl : std_logic;
    signal dac_eeprom_iic_sda : std_logic;

    signal dac_1_data_buf : std_logic_vector(13 downto 0);
    signal dac_2_data_buf : std_logic_vector(13 downto 0);
    signal dac_3_data_buf : std_logic_vector(13 downto 0);
    signal dac_4_data_buf : std_logic_vector(13 downto 0);
begin
    top : entity work.top port map(
        clk => sys_clk,
        rst => sys_rst_bar,
        txd => uart_txd,
        rxd => uart_rxd,

        -- adc not connected to physical ports yet
        adc_in_0 => (others => '0'),
        adc_in_1 => (others => '0'),
        adc_in_2 => (others => '0'),
        adc_in_3 => (others => '0'),

        dac_out_0 => dac_1_data_buf,
        dac_out_1 => dac_2_data_buf,
        dac_out_2 => dac_3_data_buf,
        dac_out_3 => dac_4_data_buf
    );

    -- leds
    led_1 <= not uart_rxd; -- detects input bit flow
    led_2 <= not uart_txd; -- detects output bit flow
    led_3 <= '1'; -- detects if the system is running
    led_4 <= sys_rst_bar; -- detects if the system is reset
    panel_led_1 <= '1';
    panel_led_2 <= '0';

    -- Interface to FL9781
    -- Align data transferred with lvds data clock
    dac_1_2_data_p_h <= dac_1_data_buf;
    dac_1_2_data_p_l <= dac_2_data_buf;
    dac_1_2_data_n_h <= not dac_1_data_buf;
    dac_1_2_data_n_l <= not dac_2_data_buf;
    dac_3_4_data_p_h <= dac_3_data_buf;
    dac_3_4_data_p_l <= dac_4_data_buf;
    dac_3_4_data_n_h <= not dac_3_data_buf;
    dac_3_4_data_n_l <= not dac_4_data_buf;
    dac_1_2_dci_p_h <= '1';
    dac_1_2_dci_p_l <= '0';
    dac_1_2_dci_n_h <= '0';
    dac_1_2_dci_n_l <= '1';
    dac_3_4_dci_p_h <= '1';
    dac_3_4_dci_p_l <= '0';
    dac_3_4_dci_n_h <= '0';
    dac_3_4_dci_n_l <= '1';
    dac_1_2_spi_ss <= '1'; -- SPI part not finished yet
    dac_3_4_spi_ss <= '1'; -- SPI part not finished yet
    dac_clk_spi_ss <= '1'; -- SPI part not finished yet
    dac_spi_sck <= '0'; -- SPI part not finished yet
    dac_spi_mosi <= '0'; -- SPI part not finished yet
    dac_eeprom_iic_scl <= '1'; -- EEPROM part not finished yet
    dac_eeprom_iic_sda <= '0'; -- EEPROM part not finished yet

    -- IO buffers
    -- clk
    sys_clk_ibufds : IBUFDS port map(
        O => sys_clk,
        I => sys_clk_p,
        IB => sys_clk_n
    );

    --rst
    sys_rst_ibuf : IBUF port map(
        O => sys_rst,
        I => rst
    );
    sys_rst_bar <= not sys_rst;

    -- leds
    led_1_obuf : OBUF port map(
        O => led_1_o,
        I => led_1
    );
    led_2_obuf : OBUF port map(
        O => led_2_o,
        I => led_2
    );
    led_3_obuf : OBUF port map(
        O => led_3_o,
        I => led_3
    );
    led_4_obuf : OBUF port map(
        O => led_4_o,
        I => led_4
    );
    panel_led_1_obuf : OBUF port map(
        O => panel_led_1_o,
        I => panel_led_1
    );
    panel_led_2_obuf : OBUF port map(
        O => panel_led_2_o,
        I => panel_led_2
    );

    -- FL9781
    dac_1_2_dci_p_oddre1 : ODDRE1 port map(
        Q => dac_1_2_dci_p_ddr_o,
        C => sys_clk,
        D1 => dac_1_2_dci_p_h,
        D2 => dac_1_2_dci_p_l,
        SR => sys_rst_bar
    );
    dac_1_2_dci_n_oddre1 : ODDRE1 port map(
        Q => dac_1_2_dci_n_ddr_o,
        C => sys_clk,
        D1 => dac_1_2_dci_n_h,
        D2 => dac_1_2_dci_n_l,
        SR => sys_rst_bar
    );
    dac_1_2_data_p_oddre1_gen : for i in 0 to 13 generate
        dac_1_2_data_p_oddre1 : ODDRE1 port map(
            Q => dac_1_2_data_p_ddr_o(i),
            C => sys_clk,
            D1 => dac_1_2_data_p_h(i),
            D2 => dac_1_2_data_p_l(i),
            SR => sys_rst_bar
        );
    end generate dac_1_2_data_p_oddre1_gen;
    dac_1_2_data_n_oddre1_gen : for i in 0 to 13 generate
        dac_1_2_data_n_oddre1 : ODDRE1 port map(
            Q => dac_1_2_data_n_ddr_o(i),
            C => sys_clk,
            D1 => dac_1_2_data_n_h(i),
            D2 => dac_1_2_data_n_l(i),
            SR => sys_rst_bar
        );
    end generate dac_1_2_data_n_oddre1_gen;
    dac_3_4_dci_p_oddre1 : ODDRE1 port map(
        Q => dac_3_4_dci_p_ddr_o,
        C => sys_clk,
        D1 => dac_3_4_dci_p_h,
        D2 => dac_3_4_dci_p_l,
        SR => sys_rst_bar
    );
    dac_3_4_dci_n_oddre1 : ODDRE1 port map(
        Q => dac_3_4_dci_n_ddr_o,
        C => sys_clk,
        D1 => dac_3_4_dci_n_h,
        D2 => dac_3_4_dci_n_l,
        SR => sys_rst_bar
    );
    dac_3_4_data_p_oddre1_gen : for i in 0 to 13 generate
        dac_3_4_data_p_oddre1 : ODDRE1 port map(
            Q => dac_3_4_data_p_ddr_o(i),
            C => sys_clk,
            D1 => dac_3_4_data_p_h(i),
            D2 => dac_3_4_data_p_l(i),
            SR => sys_rst_bar
        );
    end generate dac_3_4_data_p_oddre1_gen;
    dac_3_4_data_n_oddre1_gen : for i in 0 to 13 generate
        dac_3_4_data_n_oddre1 : ODDRE1 port map(
            Q => dac_3_4_data_n_ddr_o(i),
            C => sys_clk,
            D1 => dac_3_4_data_n_h(i),
            D2 => dac_3_4_data_n_l(i),
            SR => sys_rst_bar
        );
    end generate dac_3_4_data_n_oddre1_gen;
    dac_1_2_spi_ss_obuf : OBUF port map(
        O => dac_1_2_spi_ss_o,
        I => dac_1_2_spi_ss
    );
    dac_3_4_spi_ss_obuf : OBUF port map(
        O => dac_3_4_spi_ss_o,
        I => dac_3_4_spi_ss
    );
    dac_clk_spi_ss_obuf : OBUF port map(
        O => dac_clk_spi_ss_o,
        I => dac_clk_spi_ss
    );
    dac_spi_sck_obuf : OBUF port map(
        O => dac_spi_sck_o,
        I => dac_spi_sck
    );
    dac_spi_mosi_obuf : OBUF port map(
        O => dac_spi_mosi_o,
        I => dac_spi_mosi
    );
    dac_eeprom_iic_scl_obuf : OBUF port map(
        O => dac_eeprom_iic_scl_o,
        I => dac_eeprom_iic_scl
    );
    dac_1_2_dco_ibufds : IBUFDS port map(
        O => dac_1_2_dco,
        I => dac_1_2_dco_p_i,
        IB => dac_1_2_dco_n_i
    );
    dac_3_4_dco_ibufds : IBUFDS port map(
        O => dac_3_4_dco,
        I => dac_3_4_dco_p_i,
        IB => dac_3_4_dco_n_i
    );
    dac_spi_miso_ibuf : IBUF port map(
        O => dac_spi_miso,
        I => dac_spi_miso_i
    );
    -- replace this with a bidirectional buffer in the future
    dac_eeprom_iic_sda_obuf : OBUF port map(
        O => dac_eeprom_iic_sda_io,
        I => dac_eeprom_iic_sda
    );
    
    -- UART
    uart_txd_obuf : OBUF port map(
        O => uart_txd_o,
        I => uart_txd
    );
    uart_rxd_ibuf : IBUF port map(
        O => uart_rxd,
        I => uart_rxd_i
    );
end architecture peripheral_wrapper;