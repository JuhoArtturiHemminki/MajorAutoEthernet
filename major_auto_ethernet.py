import numpy as np
from numba import njit, int64

@njit(fastmath=True, cache=True)
def majorautoethernet_core_engine(data_stream, mode, final_states=None):
    SHIFT = 16
    SCALE = int64(1) << SHIFT
    MASK_64 = (int64(1) << 60) - 1
    
    ETA = int64(0.005 * SCALE)
    C_COEFF = int64(0.5 * SCALE)
    
    length = len(data_stream)
    buffer_out = np.zeros(length, dtype=int64)
    
    if mode == 0:
        REG_RX  = int64(0.1 * SCALE)
        REG_RWA = int64(0.6 * SCALE)
        REG_RWB = int64(0.4 * SCALE)
    else:
        REG_RX  = final_states[0]
        REG_RWA = final_states[1]
        REG_RWB = final_states[2]

    for i in range(length):
        if mode == 0:
            bit = data_stream[i]
            x_w_b = (REG_RX * REG_RWB) >> SHIFT
            mod = (C_COEFF * (((x_w_b * x_w_b) >> SHIFT) * x_w_b) >> SHIFT) >> SHIFT
            
            new_rx = ((REG_RX * REG_RWA) >> SHIFT) + mod + (bit << SHIFT)
            new_rx &= MASK_64
            
            REG_RWA = (REG_RWA + ((ETA * ((new_rx * REG_RX) >> SHIFT)) >> SHIFT)) & MASK_64
            REG_RWB = (REG_RWB - ((ETA * ((new_rx * mod) >> SHIFT)) >> SHIFT)) & MASK_64
            
            buffer_out[i] = REG_RX
            REG_RX = new_rx
        else:
            target_x = data_stream[length - 1 - i]
            
            low_0, high_0 = -10 * SCALE, 10 * SCALE
            for _ in range(35):
                mid = (low_0 + high_0) >> 1
                val = ((mid * REG_RWA) >> SHIFT) + (C_COEFF * (((((mid * REG_RWB) >> SHIFT) ** 3) >> (SHIFT*2))))
                if val < target_x: low_0 = mid
                else: high_0 = mid
            prev_x_0 = (low_0 + high_0) >> 1
            mod_0 = (C_COEFF * (((((prev_x_0 * REG_RWB) >> SHIFT) ** 3) >> (SHIFT*2))))
            err_0 = abs(((prev_x_0 * REG_RWA) >> SHIFT) + mod_0 - target_x)
            
            low_1, high_1 = -10 * SCALE, 10 * SCALE
            for _ in range(35):
                mid = (low_1 + high_1) >> 1
                val = ((mid * REG_RWA) >> SHIFT) + (C_COEFF * (((((mid * REG_RWB) >> SHIFT) ** 3) >> (SHIFT*2)))) + (1 << SHIFT)
                if val < target_x: low_1 = mid
                else: high_1 = mid
            prev_x_1 = (low_1 + high_1) >> 1
            mod_1 = (C_COEFF * (((((prev_x_1 * REG_RWB) >> SHIFT) ** 3) >> (SHIFT*2))))
            err_1 = abs(((prev_x_1 * REG_RWA) >> SHIFT) + mod_1 + (1 << SHIFT) - target_x)
            
            if err_0 < err_1:
                chosen_bit = 0
                selected_prev_x = prev_x_0
                selected_mod = mod_0
            else:
                chosen_bit = 1
                selected_prev_x = prev_x_1
                selected_mod = mod_1
                
            buffer_out[i] = chosen_bit
            
            REG_RWA = (REG_RWA - ((ETA * ((target_x * selected_prev_x) >> SHIFT)) >> SHIFT)) & MASK_64
            REG_RWB = (REG_RWB + ((ETA * ((target_x * selected_mod) >> SHIFT)) >> SHIFT)) & MASK_64
            
    if mode == 0:
        return buffer_out, np.array([REG_RX, REG_RWA, REG_RWB], dtype=int64)
    else:
        return buffer_out
