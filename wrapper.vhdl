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
        dac_a_b_dci_p_ddr_o     :   out std_logic;
        dac_a_b_dci_n_ddr_o     :   out std_logic;
        dac_a_b_dco_p_i         :   in  std_logic;
        dac_a_b_dco_n_i         :   in  std_logic;
        dac_a_b_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_a_b_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_a_b_spi_ss_o        :   out std_logic;
        dac_c_d_dci_p_ddr_o     :   out std_logic;
        dac_c_d_dci_n_ddr_o     :   out std_logic;
        dac_c_d_dco_p_i         :   in  std_logic;
        dac_c_d_dco_n_i         :   in  std_logic;
        dac_c_d_data_p_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_c_d_data_n_ddr_o    :   out std_logic_vector(13 downto 0);
        dac_c_d_spi_ss_o        :   out std_logic;
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

    -- To register an spi module:
    -- 1.Follow the format below, connecting mosi, miso, sclk and one bit from ss to the module
    -- 2.Register the address of the module in mypak
    -- 3.Register the name of the module in uart_protocol
    -- 4.Add corresponding lines in central_control
    signal spi_mosi : std_logic;
    signal spi_miso : std_logic;
    signal spi_sclk : std_logic;
    signal spi_ss   : std_logic_vector(15 downto 0);

    signal dac_a_b_data_p_h : std_logic_vector(13 downto 0);
    signal dac_a_b_data_p_l : std_logic_vector(13 downto 0);
    signal dac_a_b_data_n_h : std_logic_vector(13 downto 0);
    signal dac_a_b_data_n_l : std_logic_vector(13 downto 0);
    signal dac_c_d_data_p_h : std_logic_vector(13 downto 0);
    signal dac_c_d_data_p_l : std_logic_vector(13 downto 0);
    signal dac_c_d_data_n_h : std_logic_vector(13 downto 0);
    signal dac_c_d_data_n_l : std_logic_vector(13 downto 0);
    signal dac_a_b_dci_p_h : std_logic;
    signal dac_a_b_dci_p_l : std_logic;
    signal dac_a_b_dci_n_h : std_logic;
    signal dac_a_b_dci_n_l : std_logic;
    signal dac_c_d_dci_p_h : std_logic;
    signal dac_c_d_dci_p_l : std_logic;
    signal dac_c_d_dci_n_h : std_logic;
    signal dac_c_d_dci_n_l : std_logic;
    signal dac_a_b_dco : std_logic;
    signal dac_c_d_dco : std_logic;
    signal dac_a_b_spi_ss : std_logic;
    signal dac_c_d_spi_ss : std_logic;
    signal dac_clk_spi_ss : std_logic;
    signal dac_spi_sck : std_logic;
    signal dac_spi_mosi : std_logic;
    signal dac_spi_miso : std_logic;
    signal dac_eeprom_iic_scl : std_logic;
    signal dac_eeprom_iic_sda : std_logic;

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_c_data_buf : std_logic_vector(13 downto 0);
    signal dac_d_data_buf : std_logic_vector(13 downto 0);
begin
    top : entity work.top port map(
        clk => sys_clk,
        rst => sys_rst_bar,
        txd => uart_txd,
        rxd => uart_rxd,

        mosi => spi_mosi,
        miso => spi_miso,
        sclk => spi_sclk,
        ss => spi_ss,

        -- adc not connected to physical ports yet
        adc_in_a => (others => '0'),
        adc_in_b => (others => '0'),
        adc_in_c => (others => '0'),
        adc_in_d => (others => '0'),

        dac_out_a => dac_a_data_buf,
        dac_out_b => dac_b_data_buf,
        dac_out_c => dac_c_data_buf,
        dac_out_d => dac_d_data_buf
    );

    -- Multiplexing SPI miso signals
    -- Using dac_spi_miso when spi_ss is selecting chips on the dac module
    spi_miso <= dac_spi_miso when spi_ss(SPI_DAC1_ADDR) = '0' or spi_ss(SPI_DAC2_ADDR) = '0' or spi_ss(SPI_CLK1_ADDR) = '0' else '0';

    -- leds
    led_1 <= not uart_rxd; -- detects input bit flow
    led_2 <= not uart_txd; -- detects output bit flow
    led_3 <= '1'; -- detects if the system is running
    led_4 <= sys_rst_bar; -- detects if the system is reset
    panel_led_1 <= '1';
    panel_led_2 <= '0';

    -- Interface to FL9781
    -- Align data transferred with lvds data clock
    dac_a_b_data_p_h <= dac_a_data_buf;
    dac_a_b_data_p_l <= dac_b_data_buf;
    dac_a_b_data_n_h <= not dac_a_data_buf;
    dac_a_b_data_n_l <= not dac_b_data_buf;
    dac_c_d_data_p_h <= dac_c_data_buf;
    dac_c_d_data_p_l <= dac_d_data_buf;
    dac_c_d_data_n_h <= not dac_c_data_buf;
    dac_c_d_data_n_l <= not dac_d_data_buf;
    dac_a_b_dci_p_h <= '1';
    dac_a_b_dci_p_l <= '0';
    dac_a_b_dci_n_h <= '0';
    dac_a_b_dci_n_l <= '1';
    dac_c_d_dci_p_h <= '1';
    dac_c_d_dci_p_l <= '0';
    dac_c_d_dci_n_h <= '0';
    dac_c_d_dci_n_l <= '1';
    dac_a_b_spi_ss <= spi_ss(SPI_DAC1_ADDR);
    dac_c_d_spi_ss <= spi_ss(SPI_DAC2_ADDR);
    dac_clk_spi_ss <= spi_ss(SPI_CLK1_ADDR);
    dac_spi_sck <= spi_sclk;
    dac_spi_mosi <= spi_mosi;
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
    dac_a_b_dci_p_oddre1 : ODDRE1 port map(
        Q => dac_a_b_dci_p_ddr_o,
        C => sys_clk,
        D1 => dac_a_b_dci_p_h,
        D2 => dac_a_b_dci_p_l,
        SR => sys_rst_bar
    );
    dac_a_b_dci_n_oddre1 : ODDRE1 port map(
        Q => dac_a_b_dci_n_ddr_o,
        C => sys_clk,
        D1 => dac_a_b_dci_n_h,
        D2 => dac_a_b_dci_n_l,
        SR => sys_rst_bar
    );
    dac_a_b_data_p_oddre1_gen : for i in 0 to 13 generate
        dac_a_b_data_p_oddre1 : ODDRE1 port map(
            Q => dac_a_b_data_p_ddr_o(i),
            C => sys_clk,
            D1 => dac_a_b_data_p_h(i),
            D2 => dac_a_b_data_p_l(i),
            SR => sys_rst_bar
        );
    end generate dac_a_b_data_p_oddre1_gen;
    dac_a_b_data_n_oddre1_gen : for i in 0 to 13 generate
        dac_a_b_data_n_oddre1 : ODDRE1 port map(
            Q => dac_a_b_data_n_ddr_o(i),
            C => sys_clk,
            D1 => dac_a_b_data_n_h(i),
            D2 => dac_a_b_data_n_l(i),
            SR => sys_rst_bar
        );
    end generate dac_a_b_data_n_oddre1_gen;
    dac_c_d_dci_p_oddre1 : ODDRE1 port map(
        Q => dac_c_d_dci_p_ddr_o,
        C => sys_clk,
        D1 => dac_c_d_dci_p_h,
        D2 => dac_c_d_dci_p_l,
        SR => sys_rst_bar
    );
    dac_c_d_dci_n_oddre1 : ODDRE1 port map(
        Q => dac_c_d_dci_n_ddr_o,
        C => sys_clk,
        D1 => dac_c_d_dci_n_h,
        D2 => dac_c_d_dci_n_l,
        SR => sys_rst_bar
    );
    dac_c_d_data_p_oddre1_gen : for i in 0 to 13 generate
        dac_c_d_data_p_oddre1 : ODDRE1 port map(
            Q => dac_c_d_data_p_ddr_o(i),
            C => sys_clk,
            D1 => dac_c_d_data_p_h(i),
            D2 => dac_c_d_data_p_l(i),
            SR => sys_rst_bar
        );
    end generate dac_c_d_data_p_oddre1_gen;
    dac_c_d_data_n_oddre1_gen : for i in 0 to 13 generate
        dac_c_d_data_n_oddre1 : ODDRE1 port map(
            Q => dac_c_d_data_n_ddr_o(i),
            C => sys_clk,
            D1 => dac_c_d_data_n_h(i),
            D2 => dac_c_d_data_n_l(i),
            SR => sys_rst_bar
        );
    end generate dac_c_d_data_n_oddre1_gen;
    dac_a_b_spi_ss_obuf : OBUF port map(
        O => dac_a_b_spi_ss_o,
        I => dac_a_b_spi_ss
    );
    dac_c_d_spi_ss_obuf : OBUF port map(
        O => dac_c_d_spi_ss_o,
        I => dac_c_d_spi_ss
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
    dac_a_b_dco_ibufds : IBUFDS port map(
        O => dac_a_b_dco,
        I => dac_a_b_dco_p_i,
        IB => dac_a_b_dco_n_i
    );
    dac_c_d_dco_ibufds : IBUFDS port map(
        O => dac_c_d_dco,
        I => dac_c_d_dco_p_i,
        IB => dac_c_d_dco_n_i
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