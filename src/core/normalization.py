import numpy as np
from quantile_filter import estimate_percentiles_blockwise
import os


# 归一化数据
def normalize(data, q_low, q_high, block_size=1024 ):
    """ 使用 2%-98% 分位数归一化，分块处理减少内存占用 """
    q2, q98 = estimate_percentiles_blockwise(data, q_low, q_high , block_size)

    print(f"估计的2%分位数: {q2}, 98%分位数: {q98}")

    if q98 == q2:
        print("Warning: 98% 和 2% 分位数相同，归一化可能失败")
        return np.zeros_like(data), q2, q98

    normalized_data = np.zeros_like(data, dtype=np.float64)
    # if os.path.exists("temp_norm.dat"):
    #     normalized_data = np.memmap("temp_norm.dat", dtype=np.float32, mode='w+', shape=data.shape)
    # else:
    #     normalized_data = np.memmap("temp_norm1.dat", dtype=np.float32, mode='w+', shape=data.shape)


    for i in range(0, data.shape[0], block_size):
        for j in range(0, data.shape[1], block_size):
            block = data[i:i + block_size, j:j + block_size]
            normalized_data[i:i + block_size, j:j + block_size] = np.clip((block - q2) / (q98 - q2), 0, 1)

    return normalized_data, q2, q98


def normalize_noq2(data, q98, q2, block_size=1024):
    """ 使用已知 q2 和 q98 进行归一化，分块处理减少内存占用 """
    if q98 == q2:
        print("Warning: 98% 和 2% 分位数相同，归一化可能失败")
        return np.zeros_like(data)  # 避免除 0

    # 预分配内存
    normalized_data = np.zeros_like(data, dtype=np.float32)

    # 分块归一化
    for i in range(0, data.shape[0], block_size):
        for j in range(0, data.shape[1], block_size):
            block = data[i:i + block_size, j:j + block_size]
            normalized_data[i:i + block_size, j:j + block_size] = np.clip((block - q2) / (q98 - q2), 0, 1)

    return normalized_data


# def normalize(data):
#     """ 使用 2%-98% 分位数归一化，避免极端值影响 """
#     q2 = np.nanpercentile(data, 2)  # 计算 2% 分位数
#     q98 = np.nanpercentile(data, 98)  # 计算 98% 分位数
#     print(f"2% 分位数: {q2}, 98% 分位数: {q98}")
#
#     if q98 == q2:
#         print("Warning: 98% 和 2% 分位数相同，归一化可能失败")
#         return np.zeros_like(data), q2, q98  # 避免除 0
#
#     # 归一化，并裁剪到 [0,1] 避免超出范围
#     normalized_data = np.clip((data - q2) / (q98 - q2), 0, 1)
#
#     return normalized_data, q2, q98
#
# def normalize_noq2(data,q98,q2):
#     # 归一化，并裁剪到 [0,1] 避免超出范围
#     normalized_data = np.clip((data - q2) / (q98 - q2), 0, 1)
#
#     return normalized_data


# 反归一化数据
def denormalize(data, min_val, max_val):
    if np.isnan(min_val) or np.isnan(max_val):
        print("Error: min_val 或 max_val 计算错误")
        return np.full_like(data, np.nan)

    result = data * (max_val - min_val) + min_val
    result_int = np.round(result).astype(np.int32)

    # 添加调试信息
    print(f"反归一化：min_val={min_val}, max_val={max_val}")
    print(f"输入数据范围: {np.min(data)} ~ {np.max(data)}")
    print(f"反归一化后数据范围: {np.min(result_int)} ~ {np.max(result_int)}")

    return result_int