import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from osgeo import gdal
from io_utils import get_geo
import os

def reproject_to_utm50(input_tif, output_tif, dst_crs):
    with rasterio.open(input_tif) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)

        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        with rasterio.open(output_tif, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )


def compare_two_projection(crs1, crs2, path1, output_dir):
    print(f"投影不同，正在转换第一幅图像到 {crs2}")
    output_path = os.path.join(output_dir, 'image1_reprojection')
    reproject_to_utm50(path1, output_path, crs2)
    path1 = output_path  # 之后使用转换后的文件
    raster1 = gdal.Open(path1)
    transform1, bound1, crs1, width1, height1 = get_geo(path1)
    return path1,raster1,transform1, bound1, crs1

