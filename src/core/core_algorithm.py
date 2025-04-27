import numpy as np
from normalization import normalize, normalize_noq2, denormalize
from overlap_utils import flatten_and_normalize
from io_utils import save_image
from scipy.optimize import minimize


# 损失函数
def loss(params, overlay_1, overlay_2):
    alpha, beta, gamma, delta = params
    print(f"Calculating loss with params: alpha={alpha}, beta={beta}, gamma={gamma}, delta={delta}")

    # 转换为 MaskArray，自动屏蔽 NaN
    overlay_1 = np.ma.masked_invalid(overlay_1)
    overlay_2 = np.ma.masked_invalid(overlay_2)

    connect_a = alpha * overlay_1 + beta
    connect_b = gamma * overlay_2 + delta
    loss_value = np.sum((connect_b - connect_a) ** 2) + np.sum((overlay_1 - connect_a) ** 2) + np.sum(
        (overlay_2 - connect_b) ** 2)

    print(f"当前损失值: {loss_value}")
    return loss_value

def process_image_in_blocks_global(image_data, alpha,beta,q_low, q_high,src_min,src_max,target_min, target_max, block_size):
    """ 以 block_size × block_size 分块处理大影像 """

    band, h, w = image_data.shape

    # 三维nanmask
    nan_mask_original = np.isnan(image_data)
    # print(f'nan-mask-original{nan_mask_original}')

    # print(f"band,h,w{band},{h},{w}")
    result = np.full_like(image_data, np.nan, dtype=np.float16)  # 创建结果影像（全 NaN）

    print("原始影像数据形状:", image_data.shape)
    print("原始影像均值（忽略 NaN）:", np.nanmean(image_data))

    # 展平图像并记录 NaN 位置
    image_flat = image_data.flatten()
    nan_mask = np.isnan(image_flat)
    valid_indices = ~nan_mask

    print("有效像素数:", np.sum(valid_indices))

    # 提取有效数据
    valid_data = image_flat[valid_indices].reshape(-1, 1)
    if valid_data.size == 0:
        print("所有数据均为 NaN，返回全 NaN 影像")
        return np.full_like(image_data, np.nan)

    print("有效数据均值:", np.mean(valid_data))

    # 检查 src_min 和 src_max
    if np.isnan(src_min) or np.isnan(src_max) or src_max == src_min:
        print("Error: src_min 和 src_max 计算错误")
        return np.full_like(image_data, np.nan)

    # 归一化（使用 clip 限制范围）
    # normalized_data = np.clip((valid_data - src_min) / (src_max - src_min), 0, 1)
    normalized_data, src_min, src_max = normalize(valid_data, q_low, q_high)

    print("归一化后数据均值:", np.nanmean(normalized_data))

    # 确保归一化后数据无 NaN
    if np.isnan(normalized_data).any():
        print("Error: 归一化数据包含 NaN")
        return np.full_like(image_data, np.nan)

    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            # 计算当前块的范围
            i_end = min(i + block_size, h)
            j_end = min(j + block_size, w)
            # print(f'normlizeddata_shape{normalized_data.shape}')

            # 提取当前块
            block = image_data[:, i:i_end, j:j_end]  # 这里改成三维，解决第一次输出后面几行都是空的问题

            processed_block = process_image_for_prediction_global(block,alpha,beta, src_min, src_max, target_min, target_max)


            # 将结果填回到对应位置
            result[:, i:i_end, j:j_end] = processed_block

            # print(f"已处理块: 行 {i}-{i_end}, 列 {j}-{j_end}")

    # 把前面得到的nanmask应用到result
    # 应用 nan_mask 确保 NaN 位置不被填充
    result[nan_mask_original] = np.nan

    return result

def global_fuse_image(overlap1, overlap2, raster1_new, raster2_new, output_dir, block_size, path1, path2, q_low, q_high, q_low_color, q_high_color,ui=None):
    # non_overlap1,q2_1,q98_1 = normalize(overlap1)
    # non_overlap2,q2_2,q98_2 = normalize(overlap2)
    norm_overlap1, norm_overlap2, min_val1, max_val1, min_val2, max_val2 = flatten_and_normalize(overlap1, overlap2, q_low, q_high,q_low_color, q_high_color)
    ui.set_progress(15)
    initial_params = (0.5, 0.5, 0.5, 0.5)
    initial_params = (1.0,0.0,1.0,0.0)

    result = minimize(loss, initial_params, args=(norm_overlap1, norm_overlap2),
                      method='L-BFGS-B', options={'disp': True, 'maxiter': 100})
    alpha, beta, gamma, delta = result.x
    ui.set_progress(65)
    # alpha, beta, gamma, delta = 1.0,0.0,1.0,0.0
    # alpha, beta, gamma, delta=(0.7241155495173619, 0.09515842448539212, 0.6510225716140998, 0.10885673018505536)

    print(f"四个校正参数alpha, beta, gamma, delta：{alpha, beta, gamma, delta}")

    processA = process_image_in_blocks_global(
        raster1_new,alpha, beta, q_low, q_high,
        src_min=min_val1, src_max=max_val1,
        target_min=min_val2, target_max=max_val2,
        block_size=block_size)
    ui.set_progress(80)

    processB = process_image_in_blocks_global(
        raster2_new,gamma, delta, q_low, q_high,
        src_min=min_val1, src_max=max_val1,
        target_min=min_val2, target_max=max_val2,
        block_size=block_size)
    ui.set_progress(95)

    save_image(f"{output_dir}/globalA2080.tif",processA,path1)
    save_image(f"{output_dir}/globalB2080.tif",processB,path2)


def process_image_for_prediction_global(image_data, alpha,beta,src_min, src_max, target_min, target_max):
    """处理整个图像数据，保留 NaN 位置，应用模型并反归一化"""
    # src_min src_max    q2和q98

    # print("原始影像数据形状:", image_data.shape)
    # print("原始影像均值（忽略 NaN）:", np.nanmean(image_data))
    #
    # 展平图像并记录 NaN 位置
    image_flat = image_data.flatten()
    nan_mask = np.isnan(image_flat)
    valid_indices = ~nan_mask

    # print("有效像素数:", np.sum(valid_indices))

    # 提取有效数据
    valid_data = image_flat[valid_indices].reshape(-1, 1)
    if valid_data.size == 0:
        # print("所有数据均为 NaN，返回全 NaN 影像")
        return np.full_like(image_data, np.nan)

    # print("有效数据均值:", np.mean(valid_data))

    # 检查 src_min 和 src_max
    if np.isnan(src_min) or np.isnan(src_max) or src_max == src_min:
        print("Error: src_min 和 src_max 计算错误")
        return np.full_like(image_data, np.nan)

    # 归一化（使用 clip 限制范围）
    # normalized_data = np.clip((valid_data - src_min) / (src_max - src_min), 0, 1)
    normalized_data = normalize_noq2(valid_data, src_max, src_min)

    # print("归一化后数据均值:", np.nanmean(normalized_data))

    # 确保归一化后数据无 NaN
    if np.isnan(normalized_data).any():
        print("Error: 归一化数据包含 NaN")
        return np.full_like(image_data, np.nan)

    # 上述只是为了要一个
    # 使用随机森林预测
    predictions_normalized = alpha * normalized_data + beta

    # 确保预测结果无 NaN
    if np.isnan(predictions_normalized).any():
        # print("Error: 预测结果包含 NaN")
        return np.full_like(image_data, np.nan)

    # print("预测结果（归一化）均值:", np.mean(predictions_normalized))

    # 检查 target_min 和 target_max
    if np.isnan(target_min) or np.isnan(target_max):
        print("Error: target_min 或 target_max 计算错误")
        return np.full_like(image_data, np.nan)

    # 反归一化（clip 限制范围）——有时候模型输出会超出理论范围
    # predictions = np.clip(predictions_normalized * (target_max - target_min) + target_min, target_min, target_max)
    # predictions = denormalize(predictions_normalized, src_min, src_max)

    # print(f"target_min: {target_min}, target_max: {target_max}")

    # 反归一化的输入参数应该是 target_min, target_max，而不是 src_min, src_max。

    # 反归一化（clip 限制范围）
    predictions = denormalize(predictions_normalized, target_min, target_max)
    predictions = np.clip(predictions, target_min, target_max)  # 避免超出范围

    # # 确保反归一化后数据无 NaN
    # if np.isnan(predictions).any():
    #     print("Error: 反归一化后仍包含 NaN")
    #     return np.full_like(image_data, np.nan)
    #
    # print("反归一化后预测值均值:", np.mean(predictions))

    # 重建完整数组
    full_prediction = np.full_like(image_flat, np.nan, dtype=np.float32)
    full_prediction[valid_indices] = predictions.flatten()
    final_image = full_prediction.reshape(image_data.shape)

    # 看一下是否有nan——应该有
    # if np.isnan(final_image).any():
    #     print("Error: 最终影像仍然包含 NaN！")
    # else:
    #     print("最终影像不包含 NaN。")
    # print("最终影像均值（忽略 NaN）:", np.nanmean(final_image))
    # 输出最终影像的统计信息
    # print("最终影像均值（忽略 NaN）:", np.nanmean(final_image))
    # print("最终影像最大值（忽略 NaN）:", np.nanmax(final_image))
    # print("最终影像最小值（忽略 NaN）:", np.nanmin(final_image))

    return final_image
