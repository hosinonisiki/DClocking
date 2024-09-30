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

        -- To serial port
        uart_txd_o      :   out std_logic;
        uart_rxd_i      :   in  std_logic;

        -- LED lights
        led_1_o         :   out std_logic;
        led_2_o         :   out std_logic;
        led_3_o         :   out std_logic;
        led_4_o         :   out std_logic;
        panel_led_1_o   :   out std_logic;
        panel_led_2_o   :   out std_logic;

        -- PIN DECLARATION GENERATION START

        fmc1_lpc_clk0_p_b : out std_logic;
        fmc1_lpc_clk0_n_b : out std_logic;
        fmc1_lpc_clk1_p_b : out std_logic;
        fmc1_lpc_clk1_n_b : out std_logic;
        fmc1_lpc_la00_p_b : out std_logic;
        fmc1_lpc_la00_n_b : out std_logic;
        fmc1_lpc_la01_p_b : out std_logic;
        fmc1_lpc_la01_n_b : out std_logic;
        fmc1_lpc_la02_p_b : out std_logic;
        fmc1_lpc_la02_n_b : out std_logic;
        fmc1_lpc_la03_p_b : out std_logic;
        fmc1_lpc_la03_n_b : out std_logic;
        fmc1_lpc_la04_p_b : out std_logic;
        fmc1_lpc_la04_n_b : out std_logic;
        fmc1_lpc_la05_p_b : out std_logic;
        fmc1_lpc_la05_n_b : out std_logic;
        fmc1_lpc_la06_p_b : out std_logic;
        fmc1_lpc_la06_n_b : out std_logic;
        fmc1_lpc_la07_p_b : out std_logic;
        fmc1_lpc_la07_n_b : out std_logic;
        fmc1_lpc_la08_p_b : out std_logic;
        fmc1_lpc_la08_n_b : out std_logic;
        fmc1_lpc_la09_p_b : out std_logic;
        fmc1_lpc_la09_n_b : out std_logic;
        fmc1_lpc_la10_p_b : out std_logic;
        fmc1_lpc_la10_n_b : out std_logic;
        fmc1_lpc_la11_p_b : out std_logic;
        fmc1_lpc_la11_n_b : out std_logic;
        fmc1_lpc_la12_p_b : out std_logic;
        fmc1_lpc_la12_n_b : out std_logic;
        fmc1_lpc_la13_p_b : out std_logic;
        fmc1_lpc_la13_n_b : out std_logic;
        fmc1_lpc_la14_p_b : out std_logic;
        fmc1_lpc_la14_n_b : out std_logic;
        fmc1_lpc_la15_p_b : out std_logic;
        fmc1_lpc_la15_n_b : out std_logic;
        fmc1_lpc_la16_p_b : out std_logic;
        fmc1_lpc_la16_n_b : out std_logic;
        fmc1_lpc_la17_p_b : out std_logic;
        fmc1_lpc_la17_n_b : out std_logic;
        fmc1_lpc_la18_p_b : out std_logic;
        fmc1_lpc_la18_n_b : out std_logic;
        fmc1_lpc_la19_p_b : out std_logic;
        fmc1_lpc_la19_n_b : out std_logic;
        fmc1_lpc_la20_p_b : out std_logic;
        fmc1_lpc_la20_n_b : out std_logic;
        fmc1_lpc_la21_p_b : out std_logic;
        fmc1_lpc_la21_n_b : out std_logic;
        fmc1_lpc_la22_p_b : out std_logic;
        fmc1_lpc_la22_n_b : out std_logic;
        fmc1_lpc_la23_p_b : out std_logic;
        fmc1_lpc_la23_n_b : out std_logic;
        fmc1_lpc_la24_p_b : out std_logic;
        fmc1_lpc_la24_n_b : out std_logic;
        fmc1_lpc_la25_p_b : out std_logic;
        fmc1_lpc_la25_n_b : out std_logic;
        fmc1_lpc_la26_p_b : out std_logic;
        fmc1_lpc_la26_n_b : out std_logic;
        fmc1_lpc_la27_p_b : out std_logic;
        fmc1_lpc_la27_n_b : out std_logic;
        fmc1_lpc_la28_p_b : out std_logic;
        fmc1_lpc_la28_n_b : out std_logic;
        fmc1_lpc_la29_p_b : out std_logic;
        fmc1_lpc_la29_n_b : out std_logic;
        fmc1_lpc_la30_p_b : out std_logic;
        fmc1_lpc_la30_n_b : out std_logic;
        fmc1_lpc_la31_p_b : out std_logic;
        fmc1_lpc_la31_n_b : out std_logic;
        fmc1_lpc_la32_p_b : out std_logic;
        fmc1_lpc_la32_n_b : out std_logic;
        fmc1_lpc_la33_p_b : out std_logic;
        fmc1_lpc_la33_n_b : out std_logic;
        fmc1_lpc_scl_b : out std_logic;
        fmc1_lpc_sda_b : out std_logic;

        fmc2_lpc_clk0_p_b : out std_logic;
        fmc2_lpc_clk0_n_b : out std_logic;
        fmc2_lpc_clk1_p_b : out std_logic;
        fmc2_lpc_clk1_n_b : out std_logic;
        fmc2_lpc_la00_p_b : in std_logic;
        fmc2_lpc_la00_n_b : in std_logic;
        fmc2_lpc_la01_p_b : out std_logic;
        fmc2_lpc_la01_n_b : out std_logic;
        fmc2_lpc_la02_p_b : in std_logic;
        fmc2_lpc_la02_n_b : in std_logic;
        fmc2_lpc_la03_p_b : out std_logic;
        fmc2_lpc_la03_n_b : inout std_logic;
        fmc2_lpc_la04_p_b : in std_logic;
        fmc2_lpc_la04_n_b : in std_logic;
        fmc2_lpc_la05_p_b : in std_logic;
        fmc2_lpc_la05_n_b : in std_logic;
        fmc2_lpc_la06_p_b : in std_logic;
        fmc2_lpc_la06_n_b : in std_logic;
        fmc2_lpc_la07_p_b : in std_logic;
        fmc2_lpc_la07_n_b : in std_logic;
        fmc2_lpc_la08_p_b : in std_logic;
        fmc2_lpc_la08_n_b : in std_logic;
        fmc2_lpc_la09_p_b : in std_logic;
        fmc2_lpc_la09_n_b : in std_logic;
        fmc2_lpc_la10_p_b : in std_logic;
        fmc2_lpc_la10_n_b : in std_logic;
        fmc2_lpc_la11_p_b : in std_logic;
        fmc2_lpc_la11_n_b : in std_logic;
        fmc2_lpc_la12_p_b : in std_logic;
        fmc2_lpc_la12_n_b : in std_logic;
        fmc2_lpc_la13_p_b : in std_logic;
        fmc2_lpc_la13_n_b : in std_logic;
        fmc2_lpc_la14_p_b : in std_logic;
        fmc2_lpc_la14_n_b : in std_logic;
        fmc2_lpc_la15_p_b : in std_logic;
        fmc2_lpc_la15_n_b : out std_logic;
        fmc2_lpc_la16_p_b : in std_logic;
        fmc2_lpc_la16_n_b : in std_logic;
        fmc2_lpc_la17_p_b : out std_logic;
        fmc2_lpc_la17_n_b : out std_logic;
        fmc2_lpc_la18_p_b : in std_logic;
        fmc2_lpc_la18_n_b : in std_logic;
        fmc2_lpc_la19_p_b : in std_logic;
        fmc2_lpc_la19_n_b : in std_logic;
        fmc2_lpc_la20_p_b : in std_logic;
        fmc2_lpc_la20_n_b : in std_logic;
        fmc2_lpc_la21_p_b : in std_logic;
        fmc2_lpc_la21_n_b : in std_logic;
        fmc2_lpc_la22_p_b : in std_logic;
        fmc2_lpc_la22_n_b : in std_logic;
        fmc2_lpc_la23_p_b : inout std_logic;
        fmc2_lpc_la23_n_b : out std_logic;
        fmc2_lpc_la24_p_b : in std_logic;
        fmc2_lpc_la24_n_b : in std_logic;
        fmc2_lpc_la25_p_b : in std_logic;
        fmc2_lpc_la25_n_b : in std_logic;
        fmc2_lpc_la26_p_b : in std_logic;
        fmc2_lpc_la26_n_b : in std_logic;
        fmc2_lpc_la27_p_b : in std_logic;
        fmc2_lpc_la27_n_b : in std_logic;
        fmc2_lpc_la28_p_b : in std_logic;
        fmc2_lpc_la28_n_b : in std_logic;
        fmc2_lpc_la29_p_b : in std_logic;
        fmc2_lpc_la29_n_b : in std_logic;
        fmc2_lpc_la30_p_b : in std_logic;
        fmc2_lpc_la30_n_b : in std_logic;
        fmc2_lpc_la31_p_b : in std_logic;
        fmc2_lpc_la31_n_b : in std_logic;
        fmc2_lpc_la32_p_b : in std_logic;
        fmc2_lpc_la32_n_b : out std_logic;
        fmc2_lpc_la33_p_b : in std_logic;
        fmc2_lpc_la33_n_b : in std_logic;
        fmc2_lpc_scl_b : out std_logic;
        fmc2_lpc_sda_b : out std_logic;

        fmc3_hpc_clk0_p_b : in std_logic;
        fmc3_hpc_clk0_n_b : in std_logic;
        fmc3_hpc_clk1_p_b : in std_logic;
        fmc3_hpc_clk1_n_b : in std_logic;
        fmc3_hpc_la00_p_b : in std_logic;
        fmc3_hpc_la00_n_b : in std_logic;
        fmc3_hpc_la01_p_b : in std_logic;
        fmc3_hpc_la01_n_b : in std_logic;
        fmc3_hpc_la02_p_b : in std_logic;
        fmc3_hpc_la02_n_b : in std_logic;
        fmc3_hpc_la03_p_b : in std_logic;
        fmc3_hpc_la03_n_b : in std_logic;
        fmc3_hpc_la04_p_b : in std_logic;
        fmc3_hpc_la04_n_b : in std_logic;
        fmc3_hpc_la05_p_b : in std_logic;
        fmc3_hpc_la05_n_b : in std_logic;
        fmc3_hpc_la06_p_b : in std_logic;
        fmc3_hpc_la06_n_b : in std_logic;
        fmc3_hpc_la07_p_b : in std_logic;
        fmc3_hpc_la07_n_b : in std_logic;
        fmc3_hpc_la08_p_b : in std_logic;
        fmc3_hpc_la08_n_b : in std_logic;
        fmc3_hpc_la09_p_b : in std_logic;
        fmc3_hpc_la09_n_b : in std_logic;
        fmc3_hpc_la10_p_b : in std_logic;
        fmc3_hpc_la10_n_b : in std_logic;
        fmc3_hpc_la11_p_b : in std_logic;
        fmc3_hpc_la11_n_b : in std_logic;
        fmc3_hpc_la12_p_b : in std_logic;
        fmc3_hpc_la12_n_b : in std_logic;
        fmc3_hpc_la13_p_b : in std_logic;
        fmc3_hpc_la13_n_b : in std_logic;
        fmc3_hpc_la14_p_b : in std_logic;
        fmc3_hpc_la14_n_b : in std_logic;
        fmc3_hpc_la15_p_b : in std_logic;
        fmc3_hpc_la15_n_b : in std_logic;
        fmc3_hpc_la16_p_b : in std_logic;
        fmc3_hpc_la16_n_b : in std_logic;
        fmc3_hpc_la17_p_b : in std_logic;
        fmc3_hpc_la17_n_b : in std_logic;
        fmc3_hpc_la18_p_b : in std_logic;
        fmc3_hpc_la18_n_b : in std_logic;
        fmc3_hpc_la19_p_b : in std_logic;
        fmc3_hpc_la19_n_b : in std_logic;
        fmc3_hpc_la20_p_b : in std_logic;
        fmc3_hpc_la20_n_b : in std_logic;
        fmc3_hpc_la21_p_b : in std_logic;
        fmc3_hpc_la21_n_b : in std_logic;
        fmc3_hpc_la22_p_b : in std_logic;
        fmc3_hpc_la22_n_b : in std_logic;
        fmc3_hpc_la23_p_b : in std_logic;
        fmc3_hpc_la23_n_b : in std_logic;
        fmc3_hpc_la24_p_b : in std_logic;
        fmc3_hpc_la24_n_b : in std_logic;
        fmc3_hpc_la25_p_b : in std_logic;
        fmc3_hpc_la25_n_b : in std_logic;
        fmc3_hpc_la26_p_b : in std_logic;
        fmc3_hpc_la26_n_b : in std_logic;
        fmc3_hpc_la27_p_b : in std_logic;
        fmc3_hpc_la27_n_b : in std_logic;
        fmc3_hpc_la28_p_b : in std_logic;
        fmc3_hpc_la28_n_b : in std_logic;
        fmc3_hpc_la29_p_b : in std_logic;
        fmc3_hpc_la29_n_b : in std_logic;
        fmc3_hpc_la30_p_b : in std_logic;
        fmc3_hpc_la30_n_b : in std_logic;
        fmc3_hpc_la31_p_b : in std_logic;
        fmc3_hpc_la31_n_b : in std_logic;
        fmc3_hpc_la32_p_b : in std_logic;
        fmc3_hpc_la32_n_b : in std_logic;
        fmc3_hpc_la33_p_b : in std_logic;
        fmc3_hpc_la33_n_b : in std_logic;
        fmc3_hpc_scl_b : in std_logic;
        fmc3_hpc_sda_b : in std_logic

        -- PIN DECLARATION GENERATION END
    );
end entity wrapper;

architecture peripheral_wrapper of wrapper is
    signal sys_clk : std_logic;
    signal sys_clk_buf : std_logic;
    signal sys_clk_125M : std_logic;
    signal sys_clk_125M_buf : std_logic;
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
    signal spi_io_tri : std_logic;

    signal dac_a_b_spi_ss : std_logic;
    signal dac_c_d_spi_ss : std_logic;
    signal dac_clk_spi_ss : std_logic;
    signal dac_spi_miso : std_logic;

    signal adc_a_b_spi_ss : std_logic;
    signal adc_c_d_spi_ss : std_logic;
    signal adc1_spi_miso : std_logic;
    signal adc2_spi_miso : std_logic;

    signal dac_a_data_buf : std_logic_vector(13 downto 0);
    signal dac_b_data_buf : std_logic_vector(13 downto 0);
    signal dac_c_data_buf : std_logic_vector(13 downto 0);
    signal dac_d_data_buf : std_logic_vector(13 downto 0);
     
    signal adc_a_data_buf : std_logic_vector(11 downto 0);
    signal adc_b_data_buf : std_logic_vector(11 downto 0);
    signal adc_c_data_buf : std_logic_vector(11 downto 0);
    signal adc_d_data_buf : std_logic_vector(11 downto 0);

    signal j2_40p           : std_logic_vector(3 to 36);
    signal j3_40p           : std_logic_vector(3 to 36);

    -- SIGNAL DECLARATION GENERATION START

    signal j2_40p_fmc_buf : std_logic_vector(3 to 36);
    signal j3_40p_fmc_buf : std_logic_vector(3 to 36);
    signal lpc240p_eeprom_iic_scl_fmc_buf : std_logic;
    signal lpc240p_eeprom_iic_sda_fmc_buf : std_logic;
    
    signal fmc1_lpc_clk0_p : std_logic;
    signal fmc1_lpc_clk0_n : std_logic;
    signal fmc1_lpc_clk1_p : std_logic;
    signal fmc1_lpc_clk1_n : std_logic;
    signal fmc1_lpc_la00_p : std_logic;
    signal fmc1_lpc_la00_n : std_logic;
    signal fmc1_lpc_la01_p : std_logic;
    signal fmc1_lpc_la01_n : std_logic;
    signal fmc1_lpc_la02_p : std_logic;
    signal fmc1_lpc_la02_n : std_logic;
    signal fmc1_lpc_la03_p : std_logic;
    signal fmc1_lpc_la03_n : std_logic;
    signal fmc1_lpc_la04_p : std_logic;
    signal fmc1_lpc_la04_n : std_logic;
    signal fmc1_lpc_la05_p : std_logic;
    signal fmc1_lpc_la05_n : std_logic;
    signal fmc1_lpc_la06_p : std_logic;
    signal fmc1_lpc_la06_n : std_logic;
    signal fmc1_lpc_la07_p : std_logic;
    signal fmc1_lpc_la07_n : std_logic;
    signal fmc1_lpc_la08_p : std_logic;
    signal fmc1_lpc_la08_n : std_logic;
    signal fmc1_lpc_la09_p : std_logic;
    signal fmc1_lpc_la09_n : std_logic;
    signal fmc1_lpc_la10_p : std_logic;
    signal fmc1_lpc_la10_n : std_logic;
    signal fmc1_lpc_la11_p : std_logic;
    signal fmc1_lpc_la11_n : std_logic;
    signal fmc1_lpc_la12_p : std_logic;
    signal fmc1_lpc_la12_n : std_logic;
    signal fmc1_lpc_la13_p : std_logic;
    signal fmc1_lpc_la13_n : std_logic;
    signal fmc1_lpc_la14_p : std_logic;
    signal fmc1_lpc_la14_n : std_logic;
    signal fmc1_lpc_la15_p : std_logic;
    signal fmc1_lpc_la15_n : std_logic;
    signal fmc1_lpc_la16_p : std_logic;
    signal fmc1_lpc_la16_n : std_logic;
    signal fmc1_lpc_la17_p : std_logic;
    signal fmc1_lpc_la17_n : std_logic;
    signal fmc1_lpc_la18_p : std_logic;
    signal fmc1_lpc_la18_n : std_logic;
    signal fmc1_lpc_la19_p : std_logic;
    signal fmc1_lpc_la19_n : std_logic;
    signal fmc1_lpc_la20_p : std_logic;
    signal fmc1_lpc_la20_n : std_logic;
    signal fmc1_lpc_la21_p : std_logic;
    signal fmc1_lpc_la21_n : std_logic;
    signal fmc1_lpc_la22_p : std_logic;
    signal fmc1_lpc_la22_n : std_logic;
    signal fmc1_lpc_la23_p : std_logic;
    signal fmc1_lpc_la23_n : std_logic;
    signal fmc1_lpc_la24_p : std_logic;
    signal fmc1_lpc_la24_n : std_logic;
    signal fmc1_lpc_la25_p : std_logic;
    signal fmc1_lpc_la25_n : std_logic;
    signal fmc1_lpc_la26_p : std_logic;
    signal fmc1_lpc_la26_n : std_logic;
    signal fmc1_lpc_la27_p : std_logic;
    signal fmc1_lpc_la27_n : std_logic;
    signal fmc1_lpc_la28_p : std_logic;
    signal fmc1_lpc_la28_n : std_logic;
    signal fmc1_lpc_la29_p : std_logic;
    signal fmc1_lpc_la29_n : std_logic;
    signal fmc1_lpc_la30_p : std_logic;
    signal fmc1_lpc_la30_n : std_logic;
    signal fmc1_lpc_la31_p : std_logic;
    signal fmc1_lpc_la31_n : std_logic;
    signal fmc1_lpc_la32_p : std_logic;
    signal fmc1_lpc_la32_n : std_logic;
    signal fmc1_lpc_la33_p : std_logic;
    signal fmc1_lpc_la33_n : std_logic;
    signal fmc1_lpc_scl : std_logic;
    signal fmc1_lpc_sda : std_logic;

    signal adc_a_b_data_fmc_buf : std_logic_vector(11 downto 0);
    signal adc_c_d_data_fmc_buf : std_logic_vector(11 downto 0);
    signal adc_a_b_dco_fmc_buf : std_logic;
    signal adc_c_d_dco_fmc_buf : std_logic;
    signal adc_a_b_spi_ss_fmc_buf : std_logic;
    signal adc_c_d_spi_ss_fmc_buf : std_logic;
    signal adc_spi_sck_fmc_buf : std_logic;
    signal adc_spi_mosi_fmc_buf : std_logic;
    signal adc1_spi_miso_fmc_buf : std_logic;
    signal adc2_spi_miso_fmc_buf : std_logic;
    signal adc_spi_io_tri_fmc_buf : std_logic;
    signal adc_clk_125M_fmc_buf : std_logic;
    signal adc_eeprom_iic_scl_fmc_buf : std_logic;
    signal adc_eeprom_iic_sda_fmc_buf : std_logic;
    
    signal fmc2_lpc_clk0_p : std_logic;
    signal fmc2_lpc_clk0_n : std_logic;
    signal fmc2_lpc_clk1_p : std_logic;
    signal fmc2_lpc_clk1_n : std_logic;
    signal fmc2_lpc_la00_buf : std_logic;
    signal fmc2_lpc_la00 : std_logic;
    signal fmc2_lpc_la01_p : std_logic;
    signal fmc2_lpc_la01_n : std_logic;
    signal fmc2_lpc_la02 : std_logic;
    signal fmc2_lpc_la03_p : std_logic;
    signal fmc2_lpc_la03_no : std_logic;
    signal fmc2_lpc_la03_ni : std_logic;
    signal fmc2_lpc_la03_nt : std_logic;
    signal fmc2_lpc_la04 : std_logic;
    signal fmc2_lpc_la05 : std_logic;
    signal fmc2_lpc_la06 : std_logic;
    signal fmc2_lpc_la07 : std_logic;
    signal fmc2_lpc_la08 : std_logic;
    signal fmc2_lpc_la09 : std_logic;
    signal fmc2_lpc_la10 : std_logic;
    signal fmc2_lpc_la11 : std_logic;
    signal fmc2_lpc_la12 : std_logic;
    signal fmc2_lpc_la13 : std_logic;
    signal fmc2_lpc_la14 : std_logic;
    signal fmc2_lpc_la15_p : std_logic;
    signal fmc2_lpc_la15_n : std_logic;
    signal fmc2_lpc_la16_p : std_logic;
    signal fmc2_lpc_la16_n : std_logic;
    signal fmc2_lpc_la17_p : std_logic;
    signal fmc2_lpc_la17_n : std_logic;
    signal fmc2_lpc_la18_buf : std_logic;
    signal fmc2_lpc_la18 : std_logic;
    signal fmc2_lpc_la19 : std_logic;
    signal fmc2_lpc_la20 : std_logic;
    signal fmc2_lpc_la21 : std_logic;
    signal fmc2_lpc_la22 : std_logic;
    signal fmc2_lpc_la23_po : std_logic;
    signal fmc2_lpc_la23_pi : std_logic;
    signal fmc2_lpc_la23_pt : std_logic;
    signal fmc2_lpc_la23_n : std_logic;
    signal fmc2_lpc_la24 : std_logic;
    signal fmc2_lpc_la25 : std_logic;
    signal fmc2_lpc_la26 : std_logic;
    signal fmc2_lpc_la27 : std_logic;
    signal fmc2_lpc_la28 : std_logic;
    signal fmc2_lpc_la29 : std_logic;
    signal fmc2_lpc_la30 : std_logic;
    signal fmc2_lpc_la31 : std_logic;
    signal fmc2_lpc_la32_p : std_logic;
    signal fmc2_lpc_la32_n : std_logic;
    signal fmc2_lpc_la33_p : std_logic;
    signal fmc2_lpc_la33_n : std_logic;
    signal fmc2_lpc_scl : std_logic;
    signal fmc2_lpc_sda : std_logic;

    
    signal fmc3_hpc_clk0_p : std_logic;
    signal fmc3_hpc_clk0_n : std_logic;
    signal fmc3_hpc_clk1_p : std_logic;
    signal fmc3_hpc_clk1_n : std_logic;
    signal fmc3_hpc_la00_p : std_logic;
    signal fmc3_hpc_la00_n : std_logic;
    signal fmc3_hpc_la01_p : std_logic;
    signal fmc3_hpc_la01_n : std_logic;
    signal fmc3_hpc_la02_p : std_logic;
    signal fmc3_hpc_la02_n : std_logic;
    signal fmc3_hpc_la03_p : std_logic;
    signal fmc3_hpc_la03_n : std_logic;
    signal fmc3_hpc_la04_p : std_logic;
    signal fmc3_hpc_la04_n : std_logic;
    signal fmc3_hpc_la05_p : std_logic;
    signal fmc3_hpc_la05_n : std_logic;
    signal fmc3_hpc_la06_p : std_logic;
    signal fmc3_hpc_la06_n : std_logic;
    signal fmc3_hpc_la07_p : std_logic;
    signal fmc3_hpc_la07_n : std_logic;
    signal fmc3_hpc_la08_p : std_logic;
    signal fmc3_hpc_la08_n : std_logic;
    signal fmc3_hpc_la09_p : std_logic;
    signal fmc3_hpc_la09_n : std_logic;
    signal fmc3_hpc_la10_p : std_logic;
    signal fmc3_hpc_la10_n : std_logic;
    signal fmc3_hpc_la11_p : std_logic;
    signal fmc3_hpc_la11_n : std_logic;
    signal fmc3_hpc_la12_p : std_logic;
    signal fmc3_hpc_la12_n : std_logic;
    signal fmc3_hpc_la13_p : std_logic;
    signal fmc3_hpc_la13_n : std_logic;
    signal fmc3_hpc_la14_p : std_logic;
    signal fmc3_hpc_la14_n : std_logic;
    signal fmc3_hpc_la15_p : std_logic;
    signal fmc3_hpc_la15_n : std_logic;
    signal fmc3_hpc_la16_p : std_logic;
    signal fmc3_hpc_la16_n : std_logic;
    signal fmc3_hpc_la17_p : std_logic;
    signal fmc3_hpc_la17_n : std_logic;
    signal fmc3_hpc_la18_p : std_logic;
    signal fmc3_hpc_la18_n : std_logic;
    signal fmc3_hpc_la19_p : std_logic;
    signal fmc3_hpc_la19_n : std_logic;
    signal fmc3_hpc_la20_p : std_logic;
    signal fmc3_hpc_la20_n : std_logic;
    signal fmc3_hpc_la21_p : std_logic;
    signal fmc3_hpc_la21_n : std_logic;
    signal fmc3_hpc_la22_p : std_logic;
    signal fmc3_hpc_la22_n : std_logic;
    signal fmc3_hpc_la23_p : std_logic;
    signal fmc3_hpc_la23_n : std_logic;
    signal fmc3_hpc_la24_p : std_logic;
    signal fmc3_hpc_la24_n : std_logic;
    signal fmc3_hpc_la25_p : std_logic;
    signal fmc3_hpc_la25_n : std_logic;
    signal fmc3_hpc_la26_p : std_logic;
    signal fmc3_hpc_la26_n : std_logic;
    signal fmc3_hpc_la27_p : std_logic;
    signal fmc3_hpc_la27_n : std_logic;
    signal fmc3_hpc_la28_p : std_logic;
    signal fmc3_hpc_la28_n : std_logic;
    signal fmc3_hpc_la29_p : std_logic;
    signal fmc3_hpc_la29_n : std_logic;
    signal fmc3_hpc_la30_p : std_logic;
    signal fmc3_hpc_la30_n : std_logic;
    signal fmc3_hpc_la31_p : std_logic;
    signal fmc3_hpc_la31_n : std_logic;
    signal fmc3_hpc_la32_p : std_logic;
    signal fmc3_hpc_la32_n : std_logic;
    signal fmc3_hpc_la33_p : std_logic;
    signal fmc3_hpc_la33_n : std_logic;
    signal fmc3_hpc_scl : std_logic;
    signal fmc3_hpc_sda : std_logic;

    -- SIGNAL DECLARATION GENERATION END

    -- Shift clock frequency from 200MHz to 250MHz, which is one half of fast dac frequency.
    signal sys_clk_locked : std_logic;
    component sys_clk_mmcm
        port (
            clk_out1            : out    std_logic;
            clk_out2            : out    std_logic;
            reset               : in     std_logic;
            locked              : out    std_logic;
            clk_in1_p           : in     std_logic;
            clk_in1_n           : in     std_logic
        );
    end component;
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
        io_tri => spi_io_tri,

        adc_in_a => adc_a_data_buf,
        adc_in_b => adc_b_data_buf,
        adc_in_c => adc_c_data_buf,
        adc_in_d => adc_d_data_buf,

        dac_out_a => dac_a_data_buf,
        dac_out_b => dac_b_data_buf,
        dac_out_c => dac_c_data_buf,
        dac_out_d => dac_d_data_buf
    );

    -- Multiplexing SPI miso signals
    -- Using dac_spi_miso when spi_ss is selecting chips on the dac module
    spi_miso <= dac_spi_miso when spi_ss(SPI_DAC1_ADDR) = '0' or spi_ss(SPI_DAC2_ADDR) = '0' or spi_ss(SPI_CLK1_ADDR) = '0' else
                adc1_spi_miso when spi_ss(SPI_ADC1_ADDR) = '0' else
                adc2_spi_miso when spi_ss(SPI_ADC2_ADDR) = '0' else
                '0';

    -- leds
    led_1 <= not uart_rxd; -- detects input bit flow
    led_2 <= not uart_txd; -- detects output bit flow
    led_3 <= spi_sclk; -- detects spi clock
    led_4 <= not (and spi_ss); -- detects if any spi chip is selected
    panel_led_1 <= '1'; -- detects if the system is running
    panel_led_2 <= sys_rst_bar; -- detects if the system is reset

    -- FL9781 adapter
    dac_a_b_spi_ss <= spi_ss(SPI_DAC1_ADDR);
    dac_c_d_spi_ss <= spi_ss(SPI_DAC2_ADDR);
    dac_clk_spi_ss <= spi_ss(SPI_CLK1_ADDR);

    -- AN9767 adapter
    AN9767_1 : entity work.AN9767_adapter(direct) port map(
        dac_a_data => dac_a_data_buf,
        dac_b_data => dac_b_data_buf,

        sys_clk => sys_clk,
        slow_dac_clk => '0',
        sys_rst => sys_rst,

        j_40p => j2_40p
    );

    AN9767_2 : entity work.AN9767_adapter(direct) port map(
        dac_a_data => dac_c_data_buf,
        dac_b_data => dac_d_data_buf,
        
        sys_clk => sys_clk,
        slow_dac_clk => '0',
        sys_rst => sys_rst,
        
        j_40p => j3_40p
    );

    -- FL9627 adapter
    adc_a_b_spi_ss <= spi_ss(SPI_ADC1_ADDR);
    adc_c_d_spi_ss <= spi_ss(SPI_ADC2_ADDR);

    -- ADAPTER INSTANTIATION GENERATION START

    FL1010 : entity work.FL1010_adapter port map(
        j2_40p => j2_40p,
        j3_40p => j3_40p,
        j2_40p_fmc => j2_40p_fmc_buf,
        j3_40p_fmc => j3_40p_fmc_buf,
        lpc240p_eeprom_iic_scl_fmc => lpc240p_eeprom_iic_scl_fmc_buf,
        lpc240p_eeprom_iic_sda_fmc => lpc240p_eeprom_iic_sda_fmc_buf
    );

    FL9627 : entity work.FL9627_adapter port map(
        adc_a_data => adc_a_data_buf,
        adc_b_data => adc_b_data_buf,
        adc_c_data => adc_c_data_buf,
        adc_d_data => adc_d_data_buf,
        adc_a_b_spi_ss => adc_a_b_spi_ss,
        adc_c_d_spi_ss => adc_c_d_spi_ss,
        adc_spi_sck => spi_sclk,
        adc_spi_mosi => spi_mosi,
        adc1_spi_miso => adc1_spi_miso,
        adc2_spi_miso => adc2_spi_miso,
        adc_spi_io_tri => spi_io_tri,
        sys_clk => sys_clk,
        adc_clk_125M => sys_clk_125M,
        sys_rst => sys_rst,
        adc_a_b_data_fmc => adc_a_b_data_fmc_buf,
        adc_c_d_data_fmc => adc_c_d_data_fmc_buf,
        adc_a_b_dco_fmc => adc_a_b_dco_fmc_buf,
        adc_c_d_dco_fmc => adc_c_d_dco_fmc_buf,
        adc_a_b_spi_ss_fmc => adc_a_b_spi_ss_fmc_buf,
        adc_c_d_spi_ss_fmc => adc_c_d_spi_ss_fmc_buf,
        adc_spi_sck_fmc => adc_spi_sck_fmc_buf,
        adc_spi_mosi_fmc => adc_spi_mosi_fmc_buf,
        adc1_spi_miso_fmc => adc1_spi_miso_fmc_buf,
        adc2_spi_miso_fmc => adc2_spi_miso_fmc_buf,
        adc_spi_io_tri_fmc => adc_spi_io_tri_fmc_buf,
        adc_clk_125M_fmc => adc_clk_125M_fmc_buf,
        adc_eeprom_iic_scl_fmc => adc_eeprom_iic_scl_fmc_buf,
        adc_eeprom_iic_sda_fmc => adc_eeprom_iic_sda_fmc_buf
    );

    -- Module unplugged
    -- ADAPTER INSTANTIATION GENERATION END

    -- SIGNAL ASSIGNMENT GENERATION START

    fmc1_lpc_la17_n <= j2_40p_fmc_buf(3);
    fmc1_lpc_la17_p <= j2_40p_fmc_buf(4);
    fmc1_lpc_la18_n <= j2_40p_fmc_buf(5);
    fmc1_lpc_la18_p <= j2_40p_fmc_buf(6);
    fmc1_lpc_la23_n <= j2_40p_fmc_buf(7);
    fmc1_lpc_la23_p <= j2_40p_fmc_buf(8);
    fmc1_lpc_la26_n <= j2_40p_fmc_buf(9);
    fmc1_lpc_la26_p <= j2_40p_fmc_buf(10);
    fmc1_lpc_la27_n <= j2_40p_fmc_buf(11);
    fmc1_lpc_la27_p <= j2_40p_fmc_buf(12);
    fmc1_lpc_la28_n <= j2_40p_fmc_buf(13);
    fmc1_lpc_la28_p <= j2_40p_fmc_buf(14);
    fmc1_lpc_la29_n <= j2_40p_fmc_buf(15);
    fmc1_lpc_la29_p <= j2_40p_fmc_buf(16);
    fmc1_lpc_la24_n <= j2_40p_fmc_buf(17);
    fmc1_lpc_la24_p <= j2_40p_fmc_buf(18);
    fmc1_lpc_la25_n <= j2_40p_fmc_buf(19);
    fmc1_lpc_la25_p <= j2_40p_fmc_buf(20);
    fmc1_lpc_la21_n <= j2_40p_fmc_buf(21);
    fmc1_lpc_la21_p <= j2_40p_fmc_buf(22);
    fmc1_lpc_la22_n <= j2_40p_fmc_buf(23);
    fmc1_lpc_la22_p <= j2_40p_fmc_buf(24);
    fmc1_lpc_la31_n <= j2_40p_fmc_buf(25);
    fmc1_lpc_la31_p <= j2_40p_fmc_buf(26);
    fmc1_lpc_la30_n <= j2_40p_fmc_buf(27);
    fmc1_lpc_la30_p <= j2_40p_fmc_buf(28);
    fmc1_lpc_la33_n <= j2_40p_fmc_buf(29);
    fmc1_lpc_la33_p <= j2_40p_fmc_buf(30);
    fmc1_lpc_la32_n <= j2_40p_fmc_buf(31);
    fmc1_lpc_la32_p <= j2_40p_fmc_buf(32);
    fmc1_lpc_la19_n <= j2_40p_fmc_buf(33);
    fmc1_lpc_la19_p <= j2_40p_fmc_buf(34);
    fmc1_lpc_la20_n <= j2_40p_fmc_buf(35);
    fmc1_lpc_la20_p <= j2_40p_fmc_buf(36);
    fmc1_lpc_la15_n <= j3_40p_fmc_buf(3);
    fmc1_lpc_la15_p <= j3_40p_fmc_buf(4);
    fmc1_lpc_la16_n <= j3_40p_fmc_buf(5);
    fmc1_lpc_la16_p <= j3_40p_fmc_buf(6);
    fmc1_lpc_la11_n <= j3_40p_fmc_buf(7);
    fmc1_lpc_la11_p <= j3_40p_fmc_buf(8);
    fmc1_lpc_la00_n <= j3_40p_fmc_buf(9);
    fmc1_lpc_la00_p <= j3_40p_fmc_buf(10);
    fmc1_lpc_la02_n <= j3_40p_fmc_buf(11);
    fmc1_lpc_la02_p <= j3_40p_fmc_buf(12);
    fmc1_lpc_la03_n <= j3_40p_fmc_buf(13);
    fmc1_lpc_la03_p <= j3_40p_fmc_buf(14);
    fmc1_lpc_la12_n <= j3_40p_fmc_buf(15);
    fmc1_lpc_la12_p <= j3_40p_fmc_buf(16);
    fmc1_lpc_la07_n <= j3_40p_fmc_buf(17);
    fmc1_lpc_la07_p <= j3_40p_fmc_buf(18);
    fmc1_lpc_la08_n <= j3_40p_fmc_buf(19);
    fmc1_lpc_la08_p <= j3_40p_fmc_buf(20);
    fmc1_lpc_la04_n <= j3_40p_fmc_buf(21);
    fmc1_lpc_la04_p <= j3_40p_fmc_buf(22);
    fmc1_lpc_la14_n <= j3_40p_fmc_buf(23);
    fmc1_lpc_la14_p <= j3_40p_fmc_buf(24);
    fmc1_lpc_la13_n <= j3_40p_fmc_buf(25);
    fmc1_lpc_la13_p <= j3_40p_fmc_buf(26);
    fmc1_lpc_la09_n <= j3_40p_fmc_buf(27);
    fmc1_lpc_la09_p <= j3_40p_fmc_buf(28);
    fmc1_lpc_la10_n <= j3_40p_fmc_buf(29);
    fmc1_lpc_la10_p <= j3_40p_fmc_buf(30);
    fmc1_lpc_la05_n <= j3_40p_fmc_buf(31);
    fmc1_lpc_la05_p <= j3_40p_fmc_buf(32);
    fmc1_lpc_la06_n <= j3_40p_fmc_buf(33);
    fmc1_lpc_la06_p <= j3_40p_fmc_buf(34);
    fmc1_lpc_la01_n <= j3_40p_fmc_buf(35);
    fmc1_lpc_la01_p <= j3_40p_fmc_buf(36);
    fmc1_lpc_scl <= lpc240p_eeprom_iic_scl_fmc_buf;
    fmc1_lpc_sda <= lpc240p_eeprom_iic_sda_fmc_buf;

    fmc2_lpc_la01_p <= adc_clk_125M_fmc_buf;
    adc_a_b_dco_fmc_buf <= fmc2_lpc_la00;
    adc_a_b_data_fmc_buf(0) <= fmc2_lpc_la02;
    adc_a_b_data_fmc_buf(1) <= fmc2_lpc_la06;
    adc_a_b_data_fmc_buf(2) <= fmc2_lpc_la05;
    adc_a_b_data_fmc_buf(3) <= fmc2_lpc_la04;
    adc_a_b_data_fmc_buf(4) <= fmc2_lpc_la10;
    adc_a_b_data_fmc_buf(5) <= fmc2_lpc_la08;
    adc_a_b_data_fmc_buf(6) <= fmc2_lpc_la07;
    adc_a_b_data_fmc_buf(7) <= fmc2_lpc_la09;
    adc_a_b_data_fmc_buf(8) <= fmc2_lpc_la12;
    adc_a_b_data_fmc_buf(9) <= fmc2_lpc_la11;
    adc_a_b_data_fmc_buf(10) <= fmc2_lpc_la13;
    adc_a_b_data_fmc_buf(11) <= fmc2_lpc_la14;
    fmc2_lpc_la17_p <= adc_clk_125M_fmc_buf;
    adc_c_d_dco_fmc_buf <= fmc2_lpc_la18;
    adc_c_d_data_fmc_buf(0) <= fmc2_lpc_la20;
    adc_c_d_data_fmc_buf(1) <= fmc2_lpc_la19;
    adc_c_d_data_fmc_buf(2) <= fmc2_lpc_la27;
    adc_c_d_data_fmc_buf(3) <= fmc2_lpc_la22;
    adc_c_d_data_fmc_buf(4) <= fmc2_lpc_la21;
    adc_c_d_data_fmc_buf(5) <= fmc2_lpc_la26;
    adc_c_d_data_fmc_buf(6) <= fmc2_lpc_la25;
    adc_c_d_data_fmc_buf(7) <= fmc2_lpc_la24;
    adc_c_d_data_fmc_buf(8) <= fmc2_lpc_la29;
    adc_c_d_data_fmc_buf(9) <= fmc2_lpc_la28;
    adc_c_d_data_fmc_buf(10) <= fmc2_lpc_la31;
    adc_c_d_data_fmc_buf(11) <= fmc2_lpc_la30;
    fmc2_lpc_la03_p <= adc_a_b_spi_ss_fmc_buf;
    fmc2_lpc_la17_n <= adc_c_d_spi_ss_fmc_buf;
    fmc2_lpc_la01_n <= adc_spi_sck_fmc_buf;
    fmc2_lpc_la23_n <= adc_spi_sck_fmc_buf;
    fmc2_lpc_la03_no <= adc_spi_mosi_fmc_buf;
    fmc2_lpc_la23_po <= adc_spi_mosi_fmc_buf;
    adc1_spi_miso_fmc_buf <= fmc2_lpc_la03_ni;
    adc2_spi_miso_fmc_buf <= fmc2_lpc_la23_pi;
    fmc2_lpc_scl <= adc_eeprom_iic_scl_fmc_buf;
    fmc2_lpc_sda <= adc_eeprom_iic_sda_fmc_buf;
    fmc2_lpc_la03_nt <= adc_spi_io_tri_fmc_buf;
    fmc2_lpc_la23_pt <= adc_spi_io_tri_fmc_buf;


    -- SIGNAL ASSIGNMENT GENERATION END

    -- io management

    -- clk
    sys_clk_mmcm_inst : sys_clk_mmcm port map(
        clk_out1 => sys_clk_buf,
        clk_out2 => sys_clk_125M_buf,
        reset => '0',
        locked => sys_clk_locked,
        clk_in1_p => sys_clk_p,
        clk_in1_n => sys_clk_n
    );
    sys_clk_bufgce : BUFGCE port map(
        O => sys_clk,
        CE => sys_clk_locked,
        I => sys_clk_buf
    );
    sys_clk_125M_bufgce : BUFGCE port map(
        O => sys_clk_125M,
        CE => sys_clk_locked,
        I => sys_clk_125M_buf
    );

    -- rst
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
    
    -- UART
    uart_txd_obuf : OBUF port map(
        O => uart_txd_o,
        I => uart_txd
    );
    uart_rxd_ibuf : IBUF port map(
        O => uart_rxd,
        I => uart_rxd_i
    );

    -- FMC LPC interface

    -- IO BUFFER GENERATION START

    fmc1_lpc_clk0_p_obuf : OBUF port map(
        I => fmc1_lpc_clk0_p,
        O => fmc1_lpc_clk0_p_b
    );
    fmc1_lpc_clk0_n_obuf : OBUF port map(
        I => fmc1_lpc_clk0_n,
        O => fmc1_lpc_clk0_n_b
    );
    fmc1_lpc_clk1_p_obuf : OBUF port map(
        I => fmc1_lpc_clk1_p,
        O => fmc1_lpc_clk1_p_b
    );
    fmc1_lpc_clk1_n_obuf : OBUF port map(
        I => fmc1_lpc_clk1_n,
        O => fmc1_lpc_clk1_n_b
    );
    fmc1_lpc_la00_p_obuf : OBUF port map(
        I => fmc1_lpc_la00_p,
        O => fmc1_lpc_la00_p_b
    );
    fmc1_lpc_la00_n_obuf : OBUF port map(
        I => fmc1_lpc_la00_n,
        O => fmc1_lpc_la00_n_b
    );
    fmc1_lpc_la01_p_obuf : OBUF port map(
        I => fmc1_lpc_la01_p,
        O => fmc1_lpc_la01_p_b
    );
    fmc1_lpc_la01_n_obuf : OBUF port map(
        I => fmc1_lpc_la01_n,
        O => fmc1_lpc_la01_n_b
    );
    fmc1_lpc_la02_p_obuf : OBUF port map(
        I => fmc1_lpc_la02_p,
        O => fmc1_lpc_la02_p_b
    );
    fmc1_lpc_la02_n_obuf : OBUF port map(
        I => fmc1_lpc_la02_n,
        O => fmc1_lpc_la02_n_b
    );
    fmc1_lpc_la03_p_obuf : OBUF port map(
        I => fmc1_lpc_la03_p,
        O => fmc1_lpc_la03_p_b
    );
    fmc1_lpc_la03_n_obuf : OBUF port map(
        I => fmc1_lpc_la03_n,
        O => fmc1_lpc_la03_n_b
    );
    fmc1_lpc_la04_p_obuf : OBUF port map(
        I => fmc1_lpc_la04_p,
        O => fmc1_lpc_la04_p_b
    );
    fmc1_lpc_la04_n_obuf : OBUF port map(
        I => fmc1_lpc_la04_n,
        O => fmc1_lpc_la04_n_b
    );
    fmc1_lpc_la05_p_obuf : OBUF port map(
        I => fmc1_lpc_la05_p,
        O => fmc1_lpc_la05_p_b
    );
    fmc1_lpc_la05_n_obuf : OBUF port map(
        I => fmc1_lpc_la05_n,
        O => fmc1_lpc_la05_n_b
    );
    fmc1_lpc_la06_p_obuf : OBUF port map(
        I => fmc1_lpc_la06_p,
        O => fmc1_lpc_la06_p_b
    );
    fmc1_lpc_la06_n_obuf : OBUF port map(
        I => fmc1_lpc_la06_n,
        O => fmc1_lpc_la06_n_b
    );
    fmc1_lpc_la07_p_obuf : OBUF port map(
        I => fmc1_lpc_la07_p,
        O => fmc1_lpc_la07_p_b
    );
    fmc1_lpc_la07_n_obuf : OBUF port map(
        I => fmc1_lpc_la07_n,
        O => fmc1_lpc_la07_n_b
    );
    fmc1_lpc_la08_p_obuf : OBUF port map(
        I => fmc1_lpc_la08_p,
        O => fmc1_lpc_la08_p_b
    );
    fmc1_lpc_la08_n_obuf : OBUF port map(
        I => fmc1_lpc_la08_n,
        O => fmc1_lpc_la08_n_b
    );
    fmc1_lpc_la09_p_obuf : OBUF port map(
        I => fmc1_lpc_la09_p,
        O => fmc1_lpc_la09_p_b
    );
    fmc1_lpc_la09_n_obuf : OBUF port map(
        I => fmc1_lpc_la09_n,
        O => fmc1_lpc_la09_n_b
    );
    fmc1_lpc_la10_p_obuf : OBUF port map(
        I => fmc1_lpc_la10_p,
        O => fmc1_lpc_la10_p_b
    );
    fmc1_lpc_la10_n_obuf : OBUF port map(
        I => fmc1_lpc_la10_n,
        O => fmc1_lpc_la10_n_b
    );
    fmc1_lpc_la11_p_obuf : OBUF port map(
        I => fmc1_lpc_la11_p,
        O => fmc1_lpc_la11_p_b
    );
    fmc1_lpc_la11_n_obuf : OBUF port map(
        I => fmc1_lpc_la11_n,
        O => fmc1_lpc_la11_n_b
    );
    fmc1_lpc_la12_p_obuf : OBUF port map(
        I => fmc1_lpc_la12_p,
        O => fmc1_lpc_la12_p_b
    );
    fmc1_lpc_la12_n_obuf : OBUF port map(
        I => fmc1_lpc_la12_n,
        O => fmc1_lpc_la12_n_b
    );
    fmc1_lpc_la13_p_obuf : OBUF port map(
        I => fmc1_lpc_la13_p,
        O => fmc1_lpc_la13_p_b
    );
    fmc1_lpc_la13_n_obuf : OBUF port map(
        I => fmc1_lpc_la13_n,
        O => fmc1_lpc_la13_n_b
    );
    fmc1_lpc_la14_p_obuf : OBUF port map(
        I => fmc1_lpc_la14_p,
        O => fmc1_lpc_la14_p_b
    );
    fmc1_lpc_la14_n_obuf : OBUF port map(
        I => fmc1_lpc_la14_n,
        O => fmc1_lpc_la14_n_b
    );
    fmc1_lpc_la15_p_obuf : OBUF port map(
        I => fmc1_lpc_la15_p,
        O => fmc1_lpc_la15_p_b
    );
    fmc1_lpc_la15_n_obuf : OBUF port map(
        I => fmc1_lpc_la15_n,
        O => fmc1_lpc_la15_n_b
    );
    fmc1_lpc_la16_p_obuf : OBUF port map(
        I => fmc1_lpc_la16_p,
        O => fmc1_lpc_la16_p_b
    );
    fmc1_lpc_la16_n_obuf : OBUF port map(
        I => fmc1_lpc_la16_n,
        O => fmc1_lpc_la16_n_b
    );
    fmc1_lpc_la17_p_obuf : OBUF port map(
        I => fmc1_lpc_la17_p,
        O => fmc1_lpc_la17_p_b
    );
    fmc1_lpc_la17_n_obuf : OBUF port map(
        I => fmc1_lpc_la17_n,
        O => fmc1_lpc_la17_n_b
    );
    fmc1_lpc_la18_p_obuf : OBUF port map(
        I => fmc1_lpc_la18_p,
        O => fmc1_lpc_la18_p_b
    );
    fmc1_lpc_la18_n_obuf : OBUF port map(
        I => fmc1_lpc_la18_n,
        O => fmc1_lpc_la18_n_b
    );
    fmc1_lpc_la19_p_obuf : OBUF port map(
        I => fmc1_lpc_la19_p,
        O => fmc1_lpc_la19_p_b
    );
    fmc1_lpc_la19_n_obuf : OBUF port map(
        I => fmc1_lpc_la19_n,
        O => fmc1_lpc_la19_n_b
    );
    fmc1_lpc_la20_p_obuf : OBUF port map(
        I => fmc1_lpc_la20_p,
        O => fmc1_lpc_la20_p_b
    );
    fmc1_lpc_la20_n_obuf : OBUF port map(
        I => fmc1_lpc_la20_n,
        O => fmc1_lpc_la20_n_b
    );
    fmc1_lpc_la21_p_obuf : OBUF port map(
        I => fmc1_lpc_la21_p,
        O => fmc1_lpc_la21_p_b
    );
    fmc1_lpc_la21_n_obuf : OBUF port map(
        I => fmc1_lpc_la21_n,
        O => fmc1_lpc_la21_n_b
    );
    fmc1_lpc_la22_p_obuf : OBUF port map(
        I => fmc1_lpc_la22_p,
        O => fmc1_lpc_la22_p_b
    );
    fmc1_lpc_la22_n_obuf : OBUF port map(
        I => fmc1_lpc_la22_n,
        O => fmc1_lpc_la22_n_b
    );
    fmc1_lpc_la23_p_obuf : OBUF port map(
        I => fmc1_lpc_la23_p,
        O => fmc1_lpc_la23_p_b
    );
    fmc1_lpc_la23_n_obuf : OBUF port map(
        I => fmc1_lpc_la23_n,
        O => fmc1_lpc_la23_n_b
    );
    fmc1_lpc_la24_p_obuf : OBUF port map(
        I => fmc1_lpc_la24_p,
        O => fmc1_lpc_la24_p_b
    );
    fmc1_lpc_la24_n_obuf : OBUF port map(
        I => fmc1_lpc_la24_n,
        O => fmc1_lpc_la24_n_b
    );
    fmc1_lpc_la25_p_obuf : OBUF port map(
        I => fmc1_lpc_la25_p,
        O => fmc1_lpc_la25_p_b
    );
    fmc1_lpc_la25_n_obuf : OBUF port map(
        I => fmc1_lpc_la25_n,
        O => fmc1_lpc_la25_n_b
    );
    fmc1_lpc_la26_p_obuf : OBUF port map(
        I => fmc1_lpc_la26_p,
        O => fmc1_lpc_la26_p_b
    );
    fmc1_lpc_la26_n_obuf : OBUF port map(
        I => fmc1_lpc_la26_n,
        O => fmc1_lpc_la26_n_b
    );
    fmc1_lpc_la27_p_obuf : OBUF port map(
        I => fmc1_lpc_la27_p,
        O => fmc1_lpc_la27_p_b
    );
    fmc1_lpc_la27_n_obuf : OBUF port map(
        I => fmc1_lpc_la27_n,
        O => fmc1_lpc_la27_n_b
    );
    fmc1_lpc_la28_p_obuf : OBUF port map(
        I => fmc1_lpc_la28_p,
        O => fmc1_lpc_la28_p_b
    );
    fmc1_lpc_la28_n_obuf : OBUF port map(
        I => fmc1_lpc_la28_n,
        O => fmc1_lpc_la28_n_b
    );
    fmc1_lpc_la29_p_obuf : OBUF port map(
        I => fmc1_lpc_la29_p,
        O => fmc1_lpc_la29_p_b
    );
    fmc1_lpc_la29_n_obuf : OBUF port map(
        I => fmc1_lpc_la29_n,
        O => fmc1_lpc_la29_n_b
    );
    fmc1_lpc_la30_p_obuf : OBUF port map(
        I => fmc1_lpc_la30_p,
        O => fmc1_lpc_la30_p_b
    );
    fmc1_lpc_la30_n_obuf : OBUF port map(
        I => fmc1_lpc_la30_n,
        O => fmc1_lpc_la30_n_b
    );
    fmc1_lpc_la31_p_obuf : OBUF port map(
        I => fmc1_lpc_la31_p,
        O => fmc1_lpc_la31_p_b
    );
    fmc1_lpc_la31_n_obuf : OBUF port map(
        I => fmc1_lpc_la31_n,
        O => fmc1_lpc_la31_n_b
    );
    fmc1_lpc_la32_p_obuf : OBUF port map(
        I => fmc1_lpc_la32_p,
        O => fmc1_lpc_la32_p_b
    );
    fmc1_lpc_la32_n_obuf : OBUF port map(
        I => fmc1_lpc_la32_n,
        O => fmc1_lpc_la32_n_b
    );
    fmc1_lpc_la33_p_obuf : OBUF port map(
        I => fmc1_lpc_la33_p,
        O => fmc1_lpc_la33_p_b
    );
    fmc1_lpc_la33_n_obuf : OBUF port map(
        I => fmc1_lpc_la33_n,
        O => fmc1_lpc_la33_n_b
    );
    fmc1_lpc_scl_obuf : OBUF port map(
        I => fmc1_lpc_scl,
        O => fmc1_lpc_scl_b
    );
    fmc1_lpc_sda_obuf : OBUF port map(
        I => fmc1_lpc_sda,
        O => fmc1_lpc_sda_b
    );

    fmc2_lpc_clk0_p_obuf : OBUF port map(
        I => fmc2_lpc_clk0_p,
        O => fmc2_lpc_clk0_p_b
    );
    fmc2_lpc_clk0_n_obuf : OBUF port map(
        I => fmc2_lpc_clk0_n,
        O => fmc2_lpc_clk0_n_b
    );
    fmc2_lpc_clk1_p_obuf : OBUF port map(
        I => fmc2_lpc_clk1_p,
        O => fmc2_lpc_clk1_p_b
    );
    fmc2_lpc_clk1_n_obuf : OBUF port map(
        I => fmc2_lpc_clk1_n,
        O => fmc2_lpc_clk1_n_b
    );
    fmc2_lpc_la00_ibufds : IBUFDS port map(
        I => fmc2_lpc_la00_p_b,
        IB => fmc2_lpc_la00_n_b,
        O => fmc2_lpc_la00_buf
    );
    fmc2_lpc_la00_bufg : BUFG port map(
        I => fmc2_lpc_la00_buf,
        O => fmc2_lpc_la00
    );
    fmc2_lpc_la01_p_obuf : OBUF port map(
        I => fmc2_lpc_la01_p,
        O => fmc2_lpc_la01_p_b
    );
    fmc2_lpc_la01_n_obuf : OBUF port map(
        I => fmc2_lpc_la01_n,
        O => fmc2_lpc_la01_n_b
    );
    fmc2_lpc_la02_ibufds : IBUFDS port map(
        I => fmc2_lpc_la02_p_b,
        IB => fmc2_lpc_la02_n_b,
        O => fmc2_lpc_la02
    );
    fmc2_lpc_la03_p_obuf : OBUF port map(
        I => fmc2_lpc_la03_p,
        O => fmc2_lpc_la03_p_b
    );
    fmc2_lpc_la03_n_iobuf : IOBUF port map(
        I => fmc2_lpc_la03_no,
        O => fmc2_lpc_la03_ni,
        IO => fmc2_lpc_la03_n_b,
        T => fmc2_lpc_la03_nt
    );
    fmc2_lpc_la04_ibufds : IBUFDS port map(
        I => fmc2_lpc_la04_p_b,
        IB => fmc2_lpc_la04_n_b,
        O => fmc2_lpc_la04
    );
    fmc2_lpc_la05_ibufds : IBUFDS port map(
        I => fmc2_lpc_la05_p_b,
        IB => fmc2_lpc_la05_n_b,
        O => fmc2_lpc_la05
    );
    fmc2_lpc_la06_ibufds : IBUFDS port map(
        I => fmc2_lpc_la06_p_b,
        IB => fmc2_lpc_la06_n_b,
        O => fmc2_lpc_la06
    );
    fmc2_lpc_la07_ibufds : IBUFDS port map(
        I => fmc2_lpc_la07_p_b,
        IB => fmc2_lpc_la07_n_b,
        O => fmc2_lpc_la07
    );
    fmc2_lpc_la08_ibufds : IBUFDS port map(
        I => fmc2_lpc_la08_p_b,
        IB => fmc2_lpc_la08_n_b,
        O => fmc2_lpc_la08
    );
    fmc2_lpc_la09_ibufds : IBUFDS port map(
        I => fmc2_lpc_la09_p_b,
        IB => fmc2_lpc_la09_n_b,
        O => fmc2_lpc_la09
    );
    fmc2_lpc_la10_ibufds : IBUFDS port map(
        I => fmc2_lpc_la10_p_b,
        IB => fmc2_lpc_la10_n_b,
        O => fmc2_lpc_la10
    );
    fmc2_lpc_la11_ibufds : IBUFDS port map(
        I => fmc2_lpc_la11_p_b,
        IB => fmc2_lpc_la11_n_b,
        O => fmc2_lpc_la11
    );
    fmc2_lpc_la12_ibufds : IBUFDS port map(
        I => fmc2_lpc_la12_p_b,
        IB => fmc2_lpc_la12_n_b,
        O => fmc2_lpc_la12
    );
    fmc2_lpc_la13_ibufds : IBUFDS port map(
        I => fmc2_lpc_la13_p_b,
        IB => fmc2_lpc_la13_n_b,
        O => fmc2_lpc_la13
    );
    fmc2_lpc_la14_ibufds : IBUFDS port map(
        I => fmc2_lpc_la14_p_b,
        IB => fmc2_lpc_la14_n_b,
        O => fmc2_lpc_la14
    );
    fmc2_lpc_la15_p_ibuf : IBUF port map(
        I => fmc2_lpc_la15_p_b,
        O => fmc2_lpc_la15_p
    );
    fmc2_lpc_la15_n_obuf : OBUF port map(
        I => fmc2_lpc_la15_n,
        O => fmc2_lpc_la15_n_b
    );
    fmc2_lpc_la16_p_ibuf : IBUF port map(
        I => fmc2_lpc_la16_p_b,
        O => fmc2_lpc_la16_p
    );
    fmc2_lpc_la16_n_ibuf : IBUF port map(
        I => fmc2_lpc_la16_n_b,
        O => fmc2_lpc_la16_n
    );
    fmc2_lpc_la17_p_obuf : OBUF port map(
        I => fmc2_lpc_la17_p,
        O => fmc2_lpc_la17_p_b
    );
    fmc2_lpc_la17_n_obuf : OBUF port map(
        I => fmc2_lpc_la17_n,
        O => fmc2_lpc_la17_n_b
    );
    fmc2_lpc_la18_ibufds : IBUFDS port map(
        I => fmc2_lpc_la18_p_b,
        IB => fmc2_lpc_la18_n_b,
        O => fmc2_lpc_la18_buf
    );
    fmc2_lpc_la18_bufg : BUFG port map(
        I => fmc2_lpc_la18_buf,
        O => fmc2_lpc_la18
    );
    fmc2_lpc_la19_ibufds : IBUFDS port map(
        I => fmc2_lpc_la19_p_b,
        IB => fmc2_lpc_la19_n_b,
        O => fmc2_lpc_la19
    );
    fmc2_lpc_la20_ibufds : IBUFDS port map(
        I => fmc2_lpc_la20_p_b,
        IB => fmc2_lpc_la20_n_b,
        O => fmc2_lpc_la20
    );
    fmc2_lpc_la21_ibufds : IBUFDS port map(
        I => fmc2_lpc_la21_p_b,
        IB => fmc2_lpc_la21_n_b,
        O => fmc2_lpc_la21
    );
    fmc2_lpc_la22_ibufds : IBUFDS port map(
        I => fmc2_lpc_la22_p_b,
        IB => fmc2_lpc_la22_n_b,
        O => fmc2_lpc_la22
    );
    fmc2_lpc_la23_p_iobuf : IOBUF port map(
        I => fmc2_lpc_la23_po,
        O => fmc2_lpc_la23_pi,
        IO => fmc2_lpc_la23_p_b,
        T => fmc2_lpc_la23_pt
    );
    fmc2_lpc_la23_n_obuf : OBUF port map(
        I => fmc2_lpc_la23_n,
        O => fmc2_lpc_la23_n_b
    );
    fmc2_lpc_la24_ibufds : IBUFDS port map(
        I => fmc2_lpc_la24_p_b,
        IB => fmc2_lpc_la24_n_b,
        O => fmc2_lpc_la24
    );
    fmc2_lpc_la25_ibufds : IBUFDS port map(
        I => fmc2_lpc_la25_p_b,
        IB => fmc2_lpc_la25_n_b,
        O => fmc2_lpc_la25
    );
    fmc2_lpc_la26_ibufds : IBUFDS port map(
        I => fmc2_lpc_la26_p_b,
        IB => fmc2_lpc_la26_n_b,
        O => fmc2_lpc_la26
    );
    fmc2_lpc_la27_ibufds : IBUFDS port map(
        I => fmc2_lpc_la27_p_b,
        IB => fmc2_lpc_la27_n_b,
        O => fmc2_lpc_la27
    );
    fmc2_lpc_la28_ibufds : IBUFDS port map(
        I => fmc2_lpc_la28_p_b,
        IB => fmc2_lpc_la28_n_b,
        O => fmc2_lpc_la28
    );
    fmc2_lpc_la29_ibufds : IBUFDS port map(
        I => fmc2_lpc_la29_p_b,
        IB => fmc2_lpc_la29_n_b,
        O => fmc2_lpc_la29
    );
    fmc2_lpc_la30_ibufds : IBUFDS port map(
        I => fmc2_lpc_la30_p_b,
        IB => fmc2_lpc_la30_n_b,
        O => fmc2_lpc_la30
    );
    fmc2_lpc_la31_ibufds : IBUFDS port map(
        I => fmc2_lpc_la31_p_b,
        IB => fmc2_lpc_la31_n_b,
        O => fmc2_lpc_la31
    );
    fmc2_lpc_la32_p_ibuf : IBUF port map(
        I => fmc2_lpc_la32_p_b,
        O => fmc2_lpc_la32_p
    );
    fmc2_lpc_la32_n_obuf : OBUF port map(
        I => fmc2_lpc_la32_n,
        O => fmc2_lpc_la32_n_b
    );
    fmc2_lpc_la33_p_ibuf : IBUF port map(
        I => fmc2_lpc_la33_p_b,
        O => fmc2_lpc_la33_p
    );
    fmc2_lpc_la33_n_ibuf : IBUF port map(
        I => fmc2_lpc_la33_n_b,
        O => fmc2_lpc_la33_n
    );
    fmc2_lpc_scl_obuf : OBUF port map(
        I => fmc2_lpc_scl,
        O => fmc2_lpc_scl_b
    );
    fmc2_lpc_sda_obuf : OBUF port map(
        I => fmc2_lpc_sda,
        O => fmc2_lpc_sda_b
    );

    fmc3_hpc_clk0_p_ibuf : IBUF port map(
        I => fmc3_hpc_clk0_p_b,
        O => fmc3_hpc_clk0_p
    );
    fmc3_hpc_clk0_n_ibuf : IBUF port map(
        I => fmc3_hpc_clk0_n_b,
        O => fmc3_hpc_clk0_n
    );
    fmc3_hpc_clk1_p_ibuf : IBUF port map(
        I => fmc3_hpc_clk1_p_b,
        O => fmc3_hpc_clk1_p
    );
    fmc3_hpc_clk1_n_ibuf : IBUF port map(
        I => fmc3_hpc_clk1_n_b,
        O => fmc3_hpc_clk1_n
    );
    fmc3_hpc_la00_p_ibuf : IBUF port map(
        I => fmc3_hpc_la00_p_b,
        O => fmc3_hpc_la00_p
    );
    fmc3_hpc_la00_n_ibuf : IBUF port map(
        I => fmc3_hpc_la00_n_b,
        O => fmc3_hpc_la00_n
    );
    fmc3_hpc_la01_p_ibuf : IBUF port map(
        I => fmc3_hpc_la01_p_b,
        O => fmc3_hpc_la01_p
    );
    fmc3_hpc_la01_n_ibuf : IBUF port map(
        I => fmc3_hpc_la01_n_b,
        O => fmc3_hpc_la01_n
    );
    fmc3_hpc_la02_p_ibuf : IBUF port map(
        I => fmc3_hpc_la02_p_b,
        O => fmc3_hpc_la02_p
    );
    fmc3_hpc_la02_n_ibuf : IBUF port map(
        I => fmc3_hpc_la02_n_b,
        O => fmc3_hpc_la02_n
    );
    fmc3_hpc_la03_p_ibuf : IBUF port map(
        I => fmc3_hpc_la03_p_b,
        O => fmc3_hpc_la03_p
    );
    fmc3_hpc_la03_n_ibuf : IBUF port map(
        I => fmc3_hpc_la03_n_b,
        O => fmc3_hpc_la03_n
    );
    fmc3_hpc_la04_p_ibuf : IBUF port map(
        I => fmc3_hpc_la04_p_b,
        O => fmc3_hpc_la04_p
    );
    fmc3_hpc_la04_n_ibuf : IBUF port map(
        I => fmc3_hpc_la04_n_b,
        O => fmc3_hpc_la04_n
    );
    fmc3_hpc_la05_p_ibuf : IBUF port map(
        I => fmc3_hpc_la05_p_b,
        O => fmc3_hpc_la05_p
    );
    fmc3_hpc_la05_n_ibuf : IBUF port map(
        I => fmc3_hpc_la05_n_b,
        O => fmc3_hpc_la05_n
    );
    fmc3_hpc_la06_p_ibuf : IBUF port map(
        I => fmc3_hpc_la06_p_b,
        O => fmc3_hpc_la06_p
    );
    fmc3_hpc_la06_n_ibuf : IBUF port map(
        I => fmc3_hpc_la06_n_b,
        O => fmc3_hpc_la06_n
    );
    fmc3_hpc_la07_p_ibuf : IBUF port map(
        I => fmc3_hpc_la07_p_b,
        O => fmc3_hpc_la07_p
    );
    fmc3_hpc_la07_n_ibuf : IBUF port map(
        I => fmc3_hpc_la07_n_b,
        O => fmc3_hpc_la07_n
    );
    fmc3_hpc_la08_p_ibuf : IBUF port map(
        I => fmc3_hpc_la08_p_b,
        O => fmc3_hpc_la08_p
    );
    fmc3_hpc_la08_n_ibuf : IBUF port map(
        I => fmc3_hpc_la08_n_b,
        O => fmc3_hpc_la08_n
    );
    fmc3_hpc_la09_p_ibuf : IBUF port map(
        I => fmc3_hpc_la09_p_b,
        O => fmc3_hpc_la09_p
    );
    fmc3_hpc_la09_n_ibuf : IBUF port map(
        I => fmc3_hpc_la09_n_b,
        O => fmc3_hpc_la09_n
    );
    fmc3_hpc_la10_p_ibuf : IBUF port map(
        I => fmc3_hpc_la10_p_b,
        O => fmc3_hpc_la10_p
    );
    fmc3_hpc_la10_n_ibuf : IBUF port map(
        I => fmc3_hpc_la10_n_b,
        O => fmc3_hpc_la10_n
    );
    fmc3_hpc_la11_p_ibuf : IBUF port map(
        I => fmc3_hpc_la11_p_b,
        O => fmc3_hpc_la11_p
    );
    fmc3_hpc_la11_n_ibuf : IBUF port map(
        I => fmc3_hpc_la11_n_b,
        O => fmc3_hpc_la11_n
    );
    fmc3_hpc_la12_p_ibuf : IBUF port map(
        I => fmc3_hpc_la12_p_b,
        O => fmc3_hpc_la12_p
    );
    fmc3_hpc_la12_n_ibuf : IBUF port map(
        I => fmc3_hpc_la12_n_b,
        O => fmc3_hpc_la12_n
    );
    fmc3_hpc_la13_p_ibuf : IBUF port map(
        I => fmc3_hpc_la13_p_b,
        O => fmc3_hpc_la13_p
    );
    fmc3_hpc_la13_n_ibuf : IBUF port map(
        I => fmc3_hpc_la13_n_b,
        O => fmc3_hpc_la13_n
    );
    fmc3_hpc_la14_p_ibuf : IBUF port map(
        I => fmc3_hpc_la14_p_b,
        O => fmc3_hpc_la14_p
    );
    fmc3_hpc_la14_n_ibuf : IBUF port map(
        I => fmc3_hpc_la14_n_b,
        O => fmc3_hpc_la14_n
    );
    fmc3_hpc_la15_p_ibuf : IBUF port map(
        I => fmc3_hpc_la15_p_b,
        O => fmc3_hpc_la15_p
    );
    fmc3_hpc_la15_n_ibuf : IBUF port map(
        I => fmc3_hpc_la15_n_b,
        O => fmc3_hpc_la15_n
    );
    fmc3_hpc_la16_p_ibuf : IBUF port map(
        I => fmc3_hpc_la16_p_b,
        O => fmc3_hpc_la16_p
    );
    fmc3_hpc_la16_n_ibuf : IBUF port map(
        I => fmc3_hpc_la16_n_b,
        O => fmc3_hpc_la16_n
    );
    fmc3_hpc_la17_p_ibuf : IBUF port map(
        I => fmc3_hpc_la17_p_b,
        O => fmc3_hpc_la17_p
    );
    fmc3_hpc_la17_n_ibuf : IBUF port map(
        I => fmc3_hpc_la17_n_b,
        O => fmc3_hpc_la17_n
    );
    fmc3_hpc_la18_p_ibuf : IBUF port map(
        I => fmc3_hpc_la18_p_b,
        O => fmc3_hpc_la18_p
    );
    fmc3_hpc_la18_n_ibuf : IBUF port map(
        I => fmc3_hpc_la18_n_b,
        O => fmc3_hpc_la18_n
    );
    fmc3_hpc_la19_p_ibuf : IBUF port map(
        I => fmc3_hpc_la19_p_b,
        O => fmc3_hpc_la19_p
    );
    fmc3_hpc_la19_n_ibuf : IBUF port map(
        I => fmc3_hpc_la19_n_b,
        O => fmc3_hpc_la19_n
    );
    fmc3_hpc_la20_p_ibuf : IBUF port map(
        I => fmc3_hpc_la20_p_b,
        O => fmc3_hpc_la20_p
    );
    fmc3_hpc_la20_n_ibuf : IBUF port map(
        I => fmc3_hpc_la20_n_b,
        O => fmc3_hpc_la20_n
    );
    fmc3_hpc_la21_p_ibuf : IBUF port map(
        I => fmc3_hpc_la21_p_b,
        O => fmc3_hpc_la21_p
    );
    fmc3_hpc_la21_n_ibuf : IBUF port map(
        I => fmc3_hpc_la21_n_b,
        O => fmc3_hpc_la21_n
    );
    fmc3_hpc_la22_p_ibuf : IBUF port map(
        I => fmc3_hpc_la22_p_b,
        O => fmc3_hpc_la22_p
    );
    fmc3_hpc_la22_n_ibuf : IBUF port map(
        I => fmc3_hpc_la22_n_b,
        O => fmc3_hpc_la22_n
    );
    fmc3_hpc_la23_p_ibuf : IBUF port map(
        I => fmc3_hpc_la23_p_b,
        O => fmc3_hpc_la23_p
    );
    fmc3_hpc_la23_n_ibuf : IBUF port map(
        I => fmc3_hpc_la23_n_b,
        O => fmc3_hpc_la23_n
    );
    fmc3_hpc_la24_p_ibuf : IBUF port map(
        I => fmc3_hpc_la24_p_b,
        O => fmc3_hpc_la24_p
    );
    fmc3_hpc_la24_n_ibuf : IBUF port map(
        I => fmc3_hpc_la24_n_b,
        O => fmc3_hpc_la24_n
    );
    fmc3_hpc_la25_p_ibuf : IBUF port map(
        I => fmc3_hpc_la25_p_b,
        O => fmc3_hpc_la25_p
    );
    fmc3_hpc_la25_n_ibuf : IBUF port map(
        I => fmc3_hpc_la25_n_b,
        O => fmc3_hpc_la25_n
    );
    fmc3_hpc_la26_p_ibuf : IBUF port map(
        I => fmc3_hpc_la26_p_b,
        O => fmc3_hpc_la26_p
    );
    fmc3_hpc_la26_n_ibuf : IBUF port map(
        I => fmc3_hpc_la26_n_b,
        O => fmc3_hpc_la26_n
    );
    fmc3_hpc_la27_p_ibuf : IBUF port map(
        I => fmc3_hpc_la27_p_b,
        O => fmc3_hpc_la27_p
    );
    fmc3_hpc_la27_n_ibuf : IBUF port map(
        I => fmc3_hpc_la27_n_b,
        O => fmc3_hpc_la27_n
    );
    fmc3_hpc_la28_p_ibuf : IBUF port map(
        I => fmc3_hpc_la28_p_b,
        O => fmc3_hpc_la28_p
    );
    fmc3_hpc_la28_n_ibuf : IBUF port map(
        I => fmc3_hpc_la28_n_b,
        O => fmc3_hpc_la28_n
    );
    fmc3_hpc_la29_p_ibuf : IBUF port map(
        I => fmc3_hpc_la29_p_b,
        O => fmc3_hpc_la29_p
    );
    fmc3_hpc_la29_n_ibuf : IBUF port map(
        I => fmc3_hpc_la29_n_b,
        O => fmc3_hpc_la29_n
    );
    fmc3_hpc_la30_p_ibuf : IBUF port map(
        I => fmc3_hpc_la30_p_b,
        O => fmc3_hpc_la30_p
    );
    fmc3_hpc_la30_n_ibuf : IBUF port map(
        I => fmc3_hpc_la30_n_b,
        O => fmc3_hpc_la30_n
    );
    fmc3_hpc_la31_p_ibuf : IBUF port map(
        I => fmc3_hpc_la31_p_b,
        O => fmc3_hpc_la31_p
    );
    fmc3_hpc_la31_n_ibuf : IBUF port map(
        I => fmc3_hpc_la31_n_b,
        O => fmc3_hpc_la31_n
    );
    fmc3_hpc_la32_p_ibuf : IBUF port map(
        I => fmc3_hpc_la32_p_b,
        O => fmc3_hpc_la32_p
    );
    fmc3_hpc_la32_n_ibuf : IBUF port map(
        I => fmc3_hpc_la32_n_b,
        O => fmc3_hpc_la32_n
    );
    fmc3_hpc_la33_p_ibuf : IBUF port map(
        I => fmc3_hpc_la33_p_b,
        O => fmc3_hpc_la33_p
    );
    fmc3_hpc_la33_n_ibuf : IBUF port map(
        I => fmc3_hpc_la33_n_b,
        O => fmc3_hpc_la33_n
    );
    fmc3_hpc_scl_ibuf : IBUF port map(
        I => fmc3_hpc_scl_b,
        O => fmc3_hpc_scl
    );
    fmc3_hpc_sda_ibuf : IBUF port map(
        I => fmc3_hpc_sda_b,
        O => fmc3_hpc_sda
    );

    -- IO BUFFER GENERATION END

end architecture peripheral_wrapper;