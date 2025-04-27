import numpy as np
import sys
import traceback

def estimate_percentiles_blockwise(data, q_low=2, q_high=98, block_size=1024):
    # total_pixels = np.count_nonzero(~np.isnan(data))
    total_pixels = 0
    for i in range(0, data.shape[0], block_size):
        for j in range(0, data.shape[1], block_size):
            block = data[i:i + block_size, j:j + block_size]
            block_flat = block.flatten()
            block_flat = block_flat[~np.isnan(block_flat)]
            total_pixels += block_flat.size
    initial_sample_per_block = 500  # 初始采样数
    min_sample_per_block = 10  # 不低于这个值
    attempt = 0

    while initial_sample_per_block >= min_sample_per_block:
        try:
            samples = []
            for i in range(0, data.shape[0], block_size):
                for j in range(0, data.shape[1], block_size):
                    block = data[i:i + block_size, j:j + block_size]
                    block_flat = block.flatten()
                    block_flat = block_flat[~np.isnan(block_flat)]
                    if block_flat.size == 0:
                        continue

                    if block_flat.size > initial_sample_per_block:
                        chosen = np.random.choice(block_flat, size=initial_sample_per_block, replace=False)
                    else:
                        chosen = block_flat

                    samples.extend(chosen)

            samples = np.array(samples)
            if samples.size == 0:
                raise ValueError("没有采样到任何有效像素")

            used_percent = (samples.size / total_pixels) * 100
            print(f"[✔] 采样成功：使用了 {samples.size} 个像素，占总有效像素的 {used_percent:.2f}%")
            q2 = np.percentile(samples, q_low)
            q98 = np.percentile(samples, q_high)
            return q2, q98

        except MemoryError:
            print(f"[⚠] 第 {attempt + 1} 次尝试时内存不足，sample_per_block={initial_sample_per_block}，尝试减半...")
            traceback.print_exc(limit=1)
            initial_sample_per_block = initial_sample_per_block // 2
            attempt += 1

    raise MemoryError(f"[✖] 即使 sample_per_block 降到 {min_sample_per_block}，仍然内存不足，采样失败。")


def filter_by_quantile(data1, data2, low=0.01, high=0.99):
    """
    :param data1:图像一
    :param data2:图像二
    :param low: 低分位数
    :param high: 高分位数
    :return: 过滤后的数据是两个数组中都符合分位数范围的部分
    """
    # mask = (~data1.mask) & (~data2.mask)
    mask = (~np.isnan(data1)) & (~np.isnan(data2))
    data1_flat = data1[mask].flatten()
    data2_flat = data2[mask].flatten()

    low = low / 100
    high = high / 100
    print(f'low:{low}')
    q1_low, q1_high = np.quantile(data1_flat, [low, high])
    q2_low, q2_high = np.quantile(data2_flat, [low, high])

    valid_mask = (data1_flat >= q1_low) & (data1_flat <= q1_high) & \
                 (data2_flat >= q2_low) & (data2_flat <= q2_high)

    print(f"Filtered data1 shape: {data1_flat[valid_mask].shape}, data2 shape: {data2_flat[valid_mask].shape}")
    print(f"Filtered data1 shape: {data1_flat[valid_mask].shape}, data2 shape: {data2_flat[valid_mask].shape}")

    return data1_flat[valid_mask], data2_flat[valid_mask]  # 过滤后的数据是两个数组中都符合分位数范围的部分。