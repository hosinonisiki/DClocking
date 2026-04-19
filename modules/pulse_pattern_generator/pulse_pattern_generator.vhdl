-- ///////////////Documentation////////////////////
-- Generates a pulse pattern composed of up to 8 line
-- segments. Each segment is described by an elapsed
-- time and a total delta on the output level.
--
-- The host pre-computes a fixed-point slope for each
-- segment so the FPGA only needs additions while the
-- segment is active. A segment with zero duration is
-- treated as an immediate jump.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity pulse_pattern_generator is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(1023 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity pulse_pattern_generator;

architecture behavioral of pulse_pattern_generator is
    type duration_array_type is array (0 to 7) of unsigned(31 downto 0);
    type delta_array_type is array (0 to 7) of signed(15 downto 0);
    type slope_array_type is array (0 to 7) of signed(31 downto 0);

    function sat16(x : signed(31 downto 0)) return signed is
        variable result : signed(15 downto 0);
    begin
        if x > to_signed(32767, 32) then
            result := to_signed(32767, 16);
        elsif x < to_signed(-32768, 32) then
            result := to_signed(-32768, 16);
        else
            result := resize(x, 16);
        end if;
        return result;
    end function;

    function sat_add16(a : signed(15 downto 0); b : signed(15 downto 0)) return signed is
    begin
        return sat16(resize(a, 32) + resize(b, 32));
    end function;

    function to_fp16_16(x : signed(15 downto 0)) return signed is
        variable result : signed(31 downto 0);
    begin
        result := shift_left(resize(x, 32), 16);
        return result;
    end function;

    signal start_cmd            : std_logic;
    signal stop_cmd             : std_logic;
    signal clear_cmd            : std_logic;
    signal repeat_count_cfg     : unsigned(31 downto 0);
    signal segment_count_cfg    : unsigned(3 downto 0);
    signal start_level_cfg      : signed(15 downto 0);
    signal idle_level_cfg       : signed(15 downto 0);
    signal hold_last_level      : std_logic;

    signal segment_duration     : duration_array_type := (others => (others => '0'));
    signal segment_delta        : delta_array_type := (others => (others => '0'));
    signal segment_slope        : slope_array_type := (others => (others => '0'));

    signal current_level_fp     : signed(31 downto 0) := (others => '0');
    signal sig_out_buf          : signed(15 downto 0) := (others => '0');

    signal active               : std_logic := '0';
    signal infinite_mode        : std_logic := '0';
    signal repeat_remaining     : unsigned(31 downto 0) := (others => '0');
    signal segment_index        : unsigned(2 downto 0) := (others => '0');
    signal cycles_remaining     : unsigned(31 downto 0) := (others => '0');
    signal target_level         : signed(15 downto 0) := (others => '0');

    signal prev_start_cmd       : std_logic := '0';
    signal prev_stop_cmd        : std_logic := '0';
    signal prev_clear_cmd       : std_logic := '0';
begin
    start_cmd <= core_param_in(0); -- address 0x00
    stop_cmd <= core_param_in(32); -- address 0x01
    clear_cmd <= core_param_in(64); -- address 0x02
    repeat_count_cfg <= unsigned(core_param_in(127 downto 96)); -- address 0x03
    segment_count_cfg <= unsigned(core_param_in(131 downto 128)); -- address 0x04
    start_level_cfg <= signed(core_param_in(175 downto 160)); -- address 0x05
    idle_level_cfg <= signed(core_param_in(207 downto 192)); -- address 0x06
    hold_last_level <= core_param_in(224); -- address 0x07

    segment_map : for i in 0 to 7 generate
    begin
        segment_duration(i) <= unsigned(core_param_in(32 * (8 + 3 * i) + 31 downto 32 * (8 + 3 * i))); -- address 0x08 + 3*i
        segment_delta(i) <= signed(core_param_in(32 * (9 + 3 * i) + 15 downto 32 * (9 + 3 * i))); -- address 0x09 + 3*i
        segment_slope(i) <= signed(core_param_in(32 * (10 + 3 * i) + 31 downto 32 * (10 + 3 * i))); -- address 0x0A + 3*i
    end generate;

    sig_out_buf <= sat16(shift_right(current_level_fp, 16));

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_out <= (others => '0');
                else
                    sig_out <= std_logic_vector(sig_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => '0') when rst = '1' else std_logic_vector(sig_out_buf);
    end generate;

    process(clk)
        variable start_edge_v        : std_logic;
        variable stop_edge_v         : std_logic;
        variable clear_edge_v        : std_logic;
        variable segment_count_v     : integer;
        variable current_seg_v       : integer;
        variable base_level_v        : signed(15 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                current_level_fp <= (others => '0');
                active <= '0';
                infinite_mode <= '0';
                repeat_remaining <= (others => '0');
                segment_index <= (others => '0');
                cycles_remaining <= (others => '0');
                target_level <= (others => '0');
                prev_start_cmd <= '0';
                prev_stop_cmd <= '0';
                prev_clear_cmd <= '0';
            else
                if start_cmd = '1' and prev_start_cmd = '0' then
                    start_edge_v := '1';
                else
                    start_edge_v := '0';
                end if;

                if stop_cmd = '1' and prev_stop_cmd = '0' then
                    stop_edge_v := '1';
                else
                    stop_edge_v := '0';
                end if;

                if clear_cmd = '1' and prev_clear_cmd = '0' then
                    clear_edge_v := '1';
                else
                    clear_edge_v := '0';
                end if;

                prev_start_cmd <= start_cmd;
                prev_stop_cmd <= stop_cmd;
                prev_clear_cmd <= clear_cmd;

                segment_count_v := to_integer(segment_count_cfg);
                if segment_count_v > 8 then
                    segment_count_v := 8;
                end if;

                if clear_edge_v = '1' or stop_edge_v = '1' then
                    active <= '0';
                    infinite_mode <= '0';
                    repeat_remaining <= (others => '0');
                    segment_index <= (others => '0');
                    cycles_remaining <= (others => '0');
                    target_level <= idle_level_cfg;
                    current_level_fp <= to_fp16_16(idle_level_cfg);

                elsif start_edge_v = '1' then
                    if segment_count_v = 0 then
                        active <= '0';
                        infinite_mode <= '0';
                        repeat_remaining <= (others => '0');
                        segment_index <= (others => '0');
                        cycles_remaining <= (others => '0');
                        target_level <= start_level_cfg;
                        current_level_fp <= to_fp16_16(start_level_cfg);
                    else
                        active <= '1';
                        infinite_mode <= '1' when repeat_count_cfg = 0 else '0';
                        repeat_remaining <= repeat_count_cfg;
                        segment_index <= (others => '0');
                        cycles_remaining <= segment_duration(0);
                        target_level <= sat_add16(start_level_cfg, segment_delta(0));
                        current_level_fp <= to_fp16_16(start_level_cfg);
                    end if;

                elsif active = '1' then
                    current_seg_v := to_integer(segment_index);

                    if current_seg_v >= segment_count_v then
                        active <= '0';
                        infinite_mode <= '0';
                        repeat_remaining <= (others => '0');
                        current_level_fp <= to_fp16_16(idle_level_cfg);
                        target_level <= idle_level_cfg;
                    elsif segment_duration(current_seg_v) = 0 or cycles_remaining = 0 or cycles_remaining = 1 then
                        base_level_v := target_level;
                        current_level_fp <= to_fp16_16(base_level_v);

                        if current_seg_v + 1 < segment_count_v then
                            segment_index <= to_unsigned(current_seg_v + 1, segment_index'length);
                            cycles_remaining <= segment_duration(current_seg_v + 1);
                            target_level <= sat_add16(base_level_v, segment_delta(current_seg_v + 1));
                        else
                            if infinite_mode = '1' or repeat_remaining > to_unsigned(1, repeat_remaining'length) then
                                if infinite_mode = '0' then
                                    repeat_remaining <= repeat_remaining - 1;
                                end if;
                                segment_index <= (others => '0');
                                cycles_remaining <= segment_duration(0);
                                target_level <= sat_add16(start_level_cfg, segment_delta(0));
                                current_level_fp <= to_fp16_16(start_level_cfg);
                            else
                                active <= '0';
                                infinite_mode <= '0';
                                repeat_remaining <= (others => '0');
                                if hold_last_level = '1' then
                                    current_level_fp <= to_fp16_16(base_level_v);
                                    target_level <= base_level_v;
                                else
                                    current_level_fp <= to_fp16_16(idle_level_cfg);
                                    target_level <= idle_level_cfg;
                                end if;
                            end if;
                        end if;
                    else
                        current_level_fp <= current_level_fp + segment_slope(current_seg_v);
                        cycles_remaining <= cycles_remaining - 1;
                    end if;
                end if;
            end if;
        end if;
    end process;
end architecture behavioral;
