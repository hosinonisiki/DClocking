library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity pdh_state_machine is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port (
        clk             : in  std_logic;  -- System clock
        rst             : in  std_logic;  -- System reset
        core_param_in   : in  std_logic_vector(255 downto 0); -- Eight 32-bit slots; addresses 0-6 are used

        -- Data flow ports (to/from signal_router)
        sig_in          : in  std_logic_vector(15 downto 0);  -- Input signal for validity check
        pid_enable      : out std_logic;  -- Active-high downstream auto-reset request when configured
        mixer_enable    : out std_logic;  -- Existing mixer control level; verify polarity at integration
        sawtooth_enable : out std_logic;  -- Active-high accumulator auto-reset request when configured
        saw_input       : in  std_logic_vector(15 downto 0)
    );
end entity pdh_state_machine;

architecture behavioral of pdh_state_machine is
    -- Internal names express the existing register meaning without changing its bus ABI.
    signal pc_cmd                   : std_logic_vector(1 downto 0);
    signal manual_loss_threshold_adc : signed(15 downto 0);
    signal manual_enter_threshold_adc: signed(15 downto 0);
    signal manual_enter_hold_cycles  : unsigned(31 downto 0);
    signal manual_loss_hold_cycles   : unsigned(31 downto 0);
    signal auto_enter_threshold_adc  : signed(15 downto 0);
    signal auto_loss_threshold_adc   : signed(15 downto 0);
    signal auto_enter_threshold_adc_buf : signed(15 downto 0);
    signal auto_loss_threshold_adc_buf  : signed(15 downto 0);
    signal auto_enter_hold_cycles    : unsigned(31 downto 0);
    signal auto_loss_hold_cycles     : unsigned(31 downto 0);
    signal max_sig_in                : signed(15 downto 0) := (15 => '1', others => '0');
    signal min_sig_in                : signed(15 downto 0) := (15 => '0', others => '1');
    signal diff_sig_in               : signed(16 downto 0); 
    signal diff_sig_in_buf           : signed(16 downto 0);
    signal scaled_lock_sig_in             : signed(32 downto 0);
    signal scaled_scan_sig_in             : signed(32 downto 0);
    signal scaled_lock_sig_in_buf    : signed(32 downto 0);
    signal scaled_scan_sig_in_buf    : signed(32 downto 0);
    signal auto_enter_ratio_q15       : signed(15 downto 0);
    signal auto_loss_ratio_q15        : signed(15 downto 0);
    constant min_AUTO_TIME            : unsigned(15 downto 0) := to_unsigned(500, 16);

    -- State machine signals
    type state_type is (IDLE, AUTO_AMP, AUTO_TIME, AUTO_WAIT,AUTO_SCANNING, SCANNING, AUTO_LOCKING, LOCKING);
    signal current_state            : state_type;
    signal condition_elapsed_cycles : unsigned(31 downto 0) := (others => '0'); -- Consecutive qualifying clocks
    signal pc_cmd_prev              : std_logic_vector(1 downto 0) := "00";

    -- Internal buffer for input
    signal sig_in_buf               : signed(15 downto 0);

    -- Sawtooth jump detection signals
    signal saw_input_signed         : signed(15 downto 0);
    signal saw_input_prev           : signed(15 downto 0) := (others => '0');
    signal sawtooth_jump            : std_logic;
    
    -- Measurement done signal
    signal measurement_done         : std_logic;


begin
    -- Preserve the 0-6 register layout: 16-bit ADC codes, 32-bit clock cycles,
    -- and signed Q1.15 fractions in the low half of their 32-bit slots.
    pc_cmd                     <= core_param_in(1 downto 0); -- 0: command request
    manual_loss_threshold_adc  <= signed(core_param_in(47 downto 32)); -- 1: above => loss condition
    manual_enter_threshold_adc <= signed(core_param_in(79 downto 64)); -- 2: below => enter condition

    manual_enter_hold_cycles   <= unsigned(core_param_in(127 downto 96)); -- 3
    manual_loss_hold_cycles    <= unsigned(core_param_in(159 downto 128)); -- 4

    auto_enter_ratio_q15       <= signed(core_param_in(175 downto 160)); -- 5: signed Q1.15
    auto_loss_ratio_q15        <= signed(core_param_in(207 downto 192)); -- 6: signed Q1.15

    saw_input_signed          <= signed(saw_input); 

    -- Optional input buffer (following project standard)
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_in_buf <= (others => '0');
                else
                    sig_in_buf <= signed(sig_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => '0') when rst = '1' else signed(sig_in);
    end generate;

    diff_sig_in_buf <= resize(max_sig_in, 17) - resize(min_sig_in, 17); -- Q17.0
    process(clk)
    begin
        if rising_edge(clk) then
            diff_sig_in <= diff_sig_in_buf;
        end if;
    end process;

    scaled_scan_sig_in_buf <= diff_sig_in * auto_enter_ratio_q15 ;-- Q18.15
    scaled_lock_sig_in_buf <= diff_sig_in * auto_loss_ratio_q15;-- Q18.15
    process(clk)
    begin
        if rising_edge(clk) then
            scaled_scan_sig_in <= scaled_scan_sig_in_buf;
            scaled_lock_sig_in <= scaled_lock_sig_in_buf;
        end if;
    end process;

    auto_enter_threshold_adc_buf <= min_sig_in + scaled_scan_sig_in(30 downto 15); -- Q16.0
    auto_loss_threshold_adc_buf <= min_sig_in + scaled_lock_sig_in(30 downto 15);

    process(clk)
    begin
        if rising_edge(clk) then
            auto_enter_threshold_adc <= auto_enter_threshold_adc_buf;
            auto_loss_threshold_adc <= auto_loss_threshold_adc_buf;
        end if;
    end process;
    
    -- Main state machine process
    state_transition: process(clk)
    begin
        if rising_edge(clk) then
            if ((saw_input_signed(15) XOR saw_input_signed (14))='1' and saw_input_signed (15) /= saw_input_prev(15)) then
                sawtooth_jump <= '1';
            else
                sawtooth_jump <= '0';
            end if;

            saw_input_prev <= saw_input_signed;

            if rst = '1'  then
                current_state <= IDLE;
                condition_elapsed_cycles <= (others => '0');
                pid_enable <= '1';
                mixer_enable <= '1';
                sawtooth_enable <= '1';
                min_sig_in <= (15 => '0', others => '1');
                max_sig_in <= (15 => '1', others => '0');
                measurement_done <= '0';
                auto_enter_hold_cycles <= (others => '0');
                auto_loss_hold_cycles <= (others => '0');
                pc_cmd_prev <= pc_cmd ; 
            else
                pc_cmd_prev <= pc_cmd;

                -- State transition logic
                case current_state is
                    when IDLE =>
                        pid_enable <= '1';
                        mixer_enable <= '1';
                        sawtooth_enable <= '1';
                        if pc_cmd = "01" and pc_cmd_prev = "00" then
                            current_state <= SCANNING;
                            condition_elapsed_cycles <= (others => '0');
                        elsif pc_cmd = "10" and pc_cmd_prev = "00" then
                            current_state <= AUTO_WAIT;
                        end if;

                    when AUTO_WAIT =>
                        pid_enable <= '1';
                        mixer_enable <= '1';
                        sawtooth_enable <= '0';
                        if pc_cmd = "00"  then 
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' then
                            current_state <= AUTO_AMP;
                            min_sig_in <= (15 => '0', others => '1');
                            max_sig_in <= (15 => '1', others => '0');
                        end if;

                    when AUTO_AMP =>
                        pid_enable <= '1';
                        mixer_enable <= '0'; 
                        sawtooth_enable <= '0';
                        
                        if sig_in_buf < min_sig_in then
                            min_sig_in <= sig_in_buf;
                        end if;
                        if sig_in_buf > max_sig_in then
                            max_sig_in <= sig_in_buf;
                        end if;
                        
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' then
                            current_state <= AUTO_TIME;
                            condition_elapsed_cycles <= (others => '0');
                            measurement_done <= '0'; 
                        end if;

                    
                    when AUTO_TIME =>
                        pid_enable <= '1';
                        mixer_enable <= '0';
                        sawtooth_enable <= '0';

                        if measurement_done = '0' then
                            if sig_in_buf < auto_enter_threshold_adc then
                                condition_elapsed_cycles <= condition_elapsed_cycles + 1;
                            else
                                if condition_elapsed_cycles > min_AUTO_TIME then
                                    measurement_done <= '1'; 
                                    auto_enter_hold_cycles <= '0' & condition_elapsed_cycles(31 downto 1);-- Existing half-duration calculation
                                    auto_loss_hold_cycles <= condition_elapsed_cycles(29 downto 0) & "00"; -- Existing fourfold-duration calculation
                                    condition_elapsed_cycles <= (others => '0');
                                else 
                                    condition_elapsed_cycles <= (others => '0');
                                end if;
                            end if;
                        end if;

                        if pc_cmd = "00" then
                            current_state <= IDLE;
                        elsif sawtooth_jump = '1' and auto_enter_hold_cycles > 0 then
                            current_state <= AUTO_SCANNING;
                            condition_elapsed_cycles <= (others => '0');
                        end if;
                    
                    when AUTO_SCANNING => 
                        mixer_enable <= '0';
                        pid_enable <= '1';
                        sawtooth_enable <= '0';
                        if sig_in_buf < auto_enter_threshold_adc then
                            if condition_elapsed_cycles < auto_enter_hold_cycles then
                                condition_elapsed_cycles <= condition_elapsed_cycles + 1;
                            else
                                current_state <= AUTO_LOCKING;
                                condition_elapsed_cycles <= (others => '0');
                            end if;
                        else
                            condition_elapsed_cycles <= (others => '0');
                        end if;
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                        end if;

                    when AUTO_LOCKING =>
                        mixer_enable    <= '0';
                        pid_enable      <= '0';
                        sawtooth_enable <= '1';
                        if pc_cmd = "00" and pc_cmd_prev = "10" then
                            current_state <= IDLE;
                            condition_elapsed_cycles <= (others => '0');
                        elsif sig_in_buf > auto_loss_threshold_adc then
                            if condition_elapsed_cycles < auto_loss_hold_cycles then
                                condition_elapsed_cycles <= condition_elapsed_cycles + 1;
                            elsif pc_cmd = "11" then
                                current_state <= IDLE;
                                condition_elapsed_cycles <= (others => '0');
                            end if;
                        else
                            condition_elapsed_cycles <= (others => '0');
                        end if;

                    --################ MANUAL MODE ################--
                    when SCANNING =>
                        mixer_enable <= '0';
                        pid_enable <= '1';
                        sawtooth_enable <= '0';
                        if sig_in_buf < manual_enter_threshold_adc then
                            if condition_elapsed_cycles < manual_enter_hold_cycles then
                                condition_elapsed_cycles <= condition_elapsed_cycles + 1;
                            else
                                current_state <= LOCKING;
                                condition_elapsed_cycles <= (others => '0');
                            end if;
                        else
                            condition_elapsed_cycles <= (others => '0');
                        end if;
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                        end if;

                    when LOCKING =>
                        mixer_enable    <= '0';
                        pid_enable      <= '0';
                        sawtooth_enable <= '1';
                        if pc_cmd = "00" and pc_cmd_prev = "01" then
                            current_state <= IDLE;
                            condition_elapsed_cycles <= (others => '0');
                        elsif sig_in_buf > manual_loss_threshold_adc then
                            if condition_elapsed_cycles < manual_loss_hold_cycles then
                                condition_elapsed_cycles <= condition_elapsed_cycles + 1;
                            else
                                current_state <= IDLE;
                                condition_elapsed_cycles <= (others => '0');
                            end if;
                        else
                            condition_elapsed_cycles <= (others => '0');
                        end if;
                end case;
            end if;
        end if;
    end process;

end architecture behavioral;
