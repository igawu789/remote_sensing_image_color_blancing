import numpy as np
import rasterio
from normalization import normalize
from quantile_filter import filter_by_quantile

def extract_overlap(image1, transform1, bound1, image2, transform2, bound2):
    # 计算公共区域的边界
    print(f'bound1,bound2{bound1},{bound2}')
    print(f'transform1,{transform1}')
    print(f'transform2,{transform2}')

    intersection_left = max(bound1.left, bound2.left)
    intersection_right = min(bound1.right, bound2.right)
    intersection_top = min(bound1.top, bound2.top)
    intersection_bottom = max(bound1.bottom, bound2.bottom)
    print(f'left,right,top,bottom{intersection_left},{intersection_right},{intersection_top},{intersection_bottom}')

    if intersection_right <= intersection_left or intersection_top <= intersection_bottom:
        raise ValueError("没有交叉区域")

    # 获取行列索引
    rowcol1_top_left = rasterio.transform.rowcol(transform1, intersection_left, intersection_top)
    rowcol1_bottom_right = rasterio.transform.rowcol(transform1, intersection_right, intersection_bottom)
    rowcol2_top_left = rasterio.transform.rowcol(transform2, intersection_left, intersection_top)
    rowcol2_bottom_right = rasterio.transform.rowcol(transform2, intersection_right, intersection_bottom)

    # # 提取公共区域数据
    # window1 = Window(rowcol1_top_left[1], rowcol1_top_left[0],
    #                  rowcol1_bottom_right[1] - rowcol1_top_left[1],
    #                  rowcol1_bottom_right[0] - rowcol1_top_left[0])
    # window2 = Window(rowcol2_top_left[1], rowcol2_top_left[0],
    #                  rowcol2_bottom_right[1] - rowcol2_top_left[1],
    #                  rowcol2_bottom_right[0] - rowcol2_top_left[0])
    # 计算窗口大小
    height1 = rowcol1_bottom_right[0] - rowcol1_top_left[0]
    width1 = rowcol1_bottom_right[1] - rowcol1_top_left[1]
    height2 = rowcol2_bottom_right[0] - rowcol2_top_left[0]
    width2 = rowcol2_bottom_right[1] - rowcol2_top_left[1]

    # 计算公共区域宽度和高度_要保证两个图像长宽一致！
    height = min(height1, height2)
    width = min(width1, width2)

    # 提取公共区域（改了一下，不知道可不可以用）
    overlap1 = [band[rowcol1_top_left[0]:rowcol1_top_left[0] + height,
                rowcol1_top_left[1]:rowcol1_top_left[1] + width] for band in image1]

    overlap2 = [band[rowcol2_top_left[0]:rowcol2_top_left[0] + height,
                rowcol2_top_left[1]:rowcol2_top_left[1] + width] for band in image2]

    # 将数据转换为 MaskedArray 并处理 NaN
    # overlap1 = np.ma.masked_invalid(overlap1)
    # overlap2 = np.ma.masked_invalid(overlap2)

    overlap1 = np.ma.filled(overlap1, np.nan)
    overlap2 = np.ma.filled(overlap2, np.nan)

    print(f"Extracted overlap shapes: {overlap1[0].shape} and {overlap2[0].shape}")
    # 打印最终的 masked 数组形状和均值
    print(f"Overlap1 masked shape: {[data.shape for data in overlap1]}")
    for i, data in enumerate(overlap1):
        print(f"Overlap1 band {i + 1} mean: {np.nanmean(data)}")

    print(f"Overlap2 masked shape: {[data.shape for data in overlap2]}")
    for i, data in enumerate(overlap2):
        print(f"Overlap2 band {i + 1} mean: {np.nanmean(data)}")
    return overlap1, overlap2


# 将数据展开并归一化,要同时删去两个图像的对应nan索引，因此要放在一个函数
def flatten_and_normalize(overlap1, overlap2,q_low, q_high, q_low_color, q_high_color):
    # 展平图像并记录 NaN 位置
    overlap1_flat = overlap1.flatten()
    overlap2_flat = overlap2.flatten()

    # 找到 overlap1 中的 NaN 值的索引
    nan_mask = np.isnan(overlap1_flat)

    # 删除 overlap1 和 overlap2 中对应的 NaN 值
    overlap1_cleaned = overlap1_flat[~nan_mask]
    overlap2_cleaned = overlap2_flat[~nan_mask]

    print(f"Shape of overlap1_cleaned after NaN removal: {overlap1_cleaned.shape}")
    print(f"Shape of overlap2_cleaned after NaN removal: {overlap2_cleaned.shape}")
    # 删除2
    nan_mask = np.isnan(overlap2_cleaned)
    overlap1_cleaned = overlap1_cleaned[~nan_mask]
    overlap2_cleaned = overlap2_cleaned[~nan_mask]

    overlap1_cleaned = overlap1_cleaned.reshape(-1, 1)
    overlap2_cleaned = overlap2_cleaned.reshape(-1, 1)
    print(f"Shape of overlap1_cleaned after NaN removal: {overlap1_cleaned.shape}")
    print(f"Shape of overlap2_cleaned after NaN removal: {overlap2_cleaned.shape}")

    nan_mask = np.isnan(overlap1_cleaned)
    valid_indices = ~nan_mask

    print("1有效像素数:", np.sum(overlap1_cleaned))

    # 提取有效数据
    valid_data = overlap1_cleaned[valid_indices].reshape(-1, 1)
    if valid_data.size == 0:
        print("1所有数据均为 NaN，返回全 NaN 影像")
        return np.full_like(overlap1, np.nan)

    print("1有效数据均值:", np.mean(valid_data))

    # 归一化（使用 clip 限制范围）
    # normalized_data = np.clip((valid_data - src_min) / (src_max - src_min), 0, 1)
    norm_overlap1, min_val1, max_val1 = normalize(valid_data, q_low, q_high)

    print("norm_overlap1归一化后数据均值:", np.nanmean(norm_overlap1))

    # 确保归一化后数据无 NaN
    if np.isnan(norm_overlap1).any():
        print("Error: norm_overlap1归一化数据包含 NaN")
        return np.full_like(overlap1, np.nan)

    nan_mask = np.isnan(overlap2_cleaned)
    valid_indices = ~nan_mask

    print("2有效像素数:", np.sum(valid_indices))

    # 提取有效数据
    valid_data = overlap2_cleaned[valid_indices].reshape(-1, 1)
    if valid_data.size == 0:
        print("2所有数据均为 NaN，返回全 NaN 影像")
        return np.full_like(overlap2, np.nan)

    print("2有效数据均值:", np.mean(valid_data))

    # 归一化（使用 clip 限制范围）
    # normalized_data = np.clip((valid_data - src_min) / (src_max - src_min), 0, 1)
    norm_overlap2, min_val2, max_val2 = normalize(valid_data,q_low, q_high)

    print("norm_overlap2归一化后数据均值:", np.nanmean(norm_overlap2))

    # 确保归一化后数据无 NaN
    if np.isnan(norm_overlap2).any():
        print("Error: norm_overlap2归一化数据包含 NaN")
        return np.full_like(overlap2, np.nan)

    norm_overlap1, norm_overlap2 = filter_by_quantile(norm_overlap1, norm_overlap2, q_low_color, q_high_color)

    return norm_overlap1, norm_overlap2, min_val1, max_val1, min_val2, max_val2