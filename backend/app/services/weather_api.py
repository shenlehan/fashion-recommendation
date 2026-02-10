import requests
from typing import Dict, Any, Optional
from app.core.config import settings


# 中文城市名到OpenWeather查询格式的映射（覆盖全国所有地级市及以上城市）
CITY_NAME_MAP = {
  # 直辖市
  "北京": "Beijing,CN",
  "上海": "Shanghai,CN",
  "天津": "Tianjin,CN",
  "重庆": "Chongqing,CN",
  
  # 河北省
  "石家庄": "Shijiazhuang,CN",
  "唐山": "Tangshan,CN",
  "秦皇岛": "Qinhuangdao,CN",
  "邯郸": "Handan,CN",
  "邢台": "Xingtai,CN",
  "保定": "Baoding,CN",
  "张家口": "Zhangjiakou,CN",
  "承德": "Chengde,CN",
  "沧州": "Cangzhou,CN",
  "廊坊": "Langfang,CN",
  "衡水": "Hengshui,CN",
  
  # 山西省
  "太原": "Taiyuan,CN",
  "大同": "Datong,CN",
  "阳泉": "Yangquan,CN",
  "长治": "Changzhi,CN",
  "晋城": "Jincheng,CN",
  "朔州": "Shuozhou,CN",
  "晋中": "Jinzhong,CN",
  "运城": "Yuncheng,CN",
  "忻州": "Xinzhou,CN",
  "临汾": "Linfen,CN",
  "吕梁": "Lvliang,CN",
  
  # 内蒙古自治区
  "呼和浩特": "Hohhot,CN",
  "包头": "Baotou,CN",
  "乌海": "Wuhai,CN",
  "赤峰": "Chifeng,CN",
  "通辽": "Tongliao,CN",
  "鄂尔多斯": "Ordos,CN",
  "呼伦贝尔": "Hulunbuir,CN",
  "巴彦淖尔": "Bayannur,CN",
  "乌兰察布": "Ulanqab,CN",
  "兴安盟": "Hinggan,CN",
  "锡林郭勒盟": "Xilin Gol,CN",
  "阿拉善盟": "Alxa,CN",
  
  # 辽宁省
  "沈阳": "Shenyang,CN",
  "大连": "Dalian,CN",
  "鞍山": "Anshan,CN",
  "抚顺": "Fushun,CN",
  "本溪": "Benxi,CN",
  "丹东": "Dandong,CN",
  "锦州": "Jinzhou,CN",
  "营口": "Yingkou,CN",
  "阜新": "Fuxin,CN",
  "辽阳": "Liaoyang,CN",
  "盘锦": "Panjin,CN",
  "铁岭": "Tieling,CN",
  "朝阳": "Chaoyang,CN",
  "葫芦岛": "Huludao,CN",
  
  # 吉林省
  "长春": "Changchun,CN",
  "吉林": "Jilin,CN",
  "四平": "Siping,CN",
  "辽源": "Liaoyuan,CN",
  "通化": "Tonghua,CN",
  "白山": "Baishan,CN",
  "松原": "Songyuan,CN",
  "白城": "Baicheng,CN",
  "延边朝鲜族自治州": "Yanbian,CN",
  
  # 黑龙江省
  "哈尔滨": "Harbin,CN",
  "齐齐哈尔": "Qiqihar,CN",
  "鸡西": "Jixi,CN",
  "鹤岗": "Hegang,CN",
  "双鸭山": "Shuangyashan,CN",
  "大庆": "Daqing,CN",
  "伊春": "Yichun,CN",
  "佳木斯": "Jiamusi,CN",
  "七台河": "Qitaihe,CN",
  "牡丹江": "Mudanjiang,CN",
  "黑河": "Heihe,CN",
  "绥化": "Suihua,CN",
  "大兴安岭地区": "Daxing'anling,CN",
  
  # 江苏省
  "南京": "Nanjing,CN",
  "无锡": "Wuxi,CN",
  "徐州": "Xuzhou,CN",
  "常州": "Changzhou,CN",
  "苏州": "Suzhou,CN",
  "南通": "Nantong,CN",
  "连云港": "Lianyungang,CN",
  "淮安": "Huai'an,CN",
  "盐城": "Yancheng,CN",
  "扬州": "Yangzhou,CN",
  "镇江": "Zhenjiang,CN",
  "泰州": "Taizhou,CN",
  "宿迁": "Suqian,CN",
  
  # 浙江省
  "杭州": "Hangzhou,CN",
  "宁波": "Ningbo,CN",
  "温州": "Wenzhou,CN",
  "嘉兴": "Jiaxing,CN",
  "湖州": "Huzhou,CN",
  "绍兴": "Shaoxing,CN",
  "金华": "Jinhua,CN",
  "衢州": "Quzhou,CN",
  "舟山": "Zhoushan,CN",
  "台州": "Taizhou,CN",
  "丽水": "Lishui,CN",
  
  # 安徽省
  "合肥": "Hefei,CN",
  "芜湖": "Wuhu,CN",
  "蚌埠": "Bengbu,CN",
  "淮南": "Huainan,CN",
  "马鞍山": "Ma'anshan,CN",
  "淮北": "Huaibei,CN",
  "铜陵": "Tongling,CN",
  "安庆": "Anqing,CN",
  "黄山": "Huangshan,CN",
  "滁州": "Chuzhou,CN",
  "阜阳": "Fuyang,CN",
  "宿州": "Suzhou,CN",
  "六安": "Lu'an,CN",
  "亳州": "Bozhou,CN",
  "池州": "Chizhou,CN",
  "宣城": "Xuancheng,CN",
  
  # 福建省
  "福州": "Fuzhou,CN",
  "厦门": "Xiamen,CN",
  "莆田": "Putian,CN",
  "三明": "Sanming,CN",
  "泉州": "Quanzhou,CN",
  "漳州": "Zhangzhou,CN",
  "南平": "Nanping,CN",
  "龙岩": "Longyan,CN",
  "宁德": "Ningde,CN",
  
  # 江西省
  "南昌": "Nanchang,CN",
  "景德镇": "Jingdezhen,CN",
  "萍乡": "Pingxiang,CN",
  "九江": "Jiujiang,CN",
  "新余": "Xinyu,CN",
  "鹰潭": "Yingtan,CN",
  "赣州": "Ganzhou,CN",
  "吉安": "Ji'an,CN",
  "宜春": "Yichun,CN",
  "抚州": "Fuzhou,CN",
  "上饶": "Shangrao,CN",
  
  # 山东省
  "济南": "Jinan,CN",
  "青岛": "Qingdao,CN",
  "淄博": "Zibo,CN",
  "枣庄": "Zaozhuang,CN",
  "东营": "Dongying,CN",
  "烟台": "Yantai,CN",
  "潍坊": "Weifang,CN",
  "济宁": "Jining,CN",
  "泰安": "Tai'an,CN",
  "威海": "Weihai,CN",
  "日照": "Rizhao,CN",
  "临沂": "Linyi,CN",
  "德州": "Dezhou,CN",
  "聊城": "Liaocheng,CN",
  "滨州": "Binzhou,CN",
  "菏泽": "Heze,CN",
  
  # 河南省
  "郑州": "Zhengzhou,CN",
  "开封": "Kaifeng,CN",
  "洛阳": "Luoyang,CN",
  "平顶山": "Pingdingshan,CN",
  "安阳": "Anyang,CN",
  "鹤壁": "Hebi,CN",
  "新乡": "Xinxiang,CN",
  "焦作": "Jiaozuo,CN",
  "濮阳": "Puyang,CN",
  "许昌": "Xuchang,CN",
  "漯河": "Luohe,CN",
  "三门峡": "Sanmenxia,CN",
  "南阳": "Nanyang,CN",
  "商丘": "Shangqiu,CN",
  "信阳": "Xinyang,CN",
  "周口": "Zhoukou,CN",
  "驻马店": "Zhumadian,CN",
  
  # 湖北省
  "武汉": "Wuhan,CN",
  "黄石": "Huangshi,CN",
  "十堰": "Shiyan,CN",
  "宜昌": "Yichang,CN",
  "襄阳": "Xiangyang,CN",
  "鄂州": "Ezhou,CN",
  "荆门": "Jingmen,CN",
  "孝感": "Xiaogan,CN",
  "荆州": "Jingzhou,CN",
  "黄冈": "Huanggang,CN",
  "咸宁": "Xianning,CN",
  "随州": "Suizhou,CN",
  "恩施土家族苗族自治州": "Enshi,CN",
  
  # 湖南省
  "长沙": "Changsha,CN",
  "株洲": "Zhuzhou,CN",
  "湘潭": "Xiangtan,CN",
  "衡阳": "Hengyang,CN",
  "邵阳": "Shaoyang,CN",
  "岳阳": "Yueyang,CN",
  "常德": "Changde,CN",
  "张家界": "Zhangjiajie,CN",
  "益阳": "Yiyang,CN",
  "郴州": "Chenzhou,CN",
  "永州": "Yongzhou,CN",
  "怀化": "Huaihua,CN",
  "娄底": "Loudi,CN",
  "湘西土家族苗族自治州": "Xiangxi,CN",
  
  # 广东省
  "广州": "Guangzhou,CN",
  "韶关": "Shaoguan,CN",
  "深圳": "Shenzhen,CN",
  "珠海": "Zhuhai,CN",
  "汕头": "Shantou,CN",
  "佛山": "Foshan,CN",
  "江门": "Jiangmen,CN",
  "湛江": "Zhanjiang,CN",
  "茂名": "Maoming,CN",
  "肇庆": "Zhaoqing,CN",
  "惠州": "Huizhou,CN",
  "梅州": "Meizhou,CN",
  "汕尾": "Shanwei,CN",
  "河源": "Heyuan,CN",
  "阳江": "Yangjiang,CN",
  "清远": "Qingyuan,CN",
  "东莞": "Dongguan,CN",
  "中山": "Zhongshan,CN",
  "潮州": "Chaozhou,CN",
  "揭阳": "Jieyang,CN",
  "云浮": "Yunfu,CN",
  
  # 广西壮族自治区
  "南宁": "Nanning,CN",
  "柳州": "Liuzhou,CN",
  "桂林": "Guilin,CN",
  "梧州": "Wuzhou,CN",
  "北海": "Beihai,CN",
  "防城港": "Fangchenggang,CN",
  "钦州": "Qinzhou,CN",
  "贵港": "Guigang,CN",
  "玉林": "Yulin,CN",
  "百色": "Baise,CN",
  "贺州": "Hezhou,CN",
  "河池": "Hechi,CN",
  "来宾": "Laibin,CN",
  "崇左": "Chongzuo,CN",
  
  # 海南省
  "海口": "Haikou,CN",
  "三亚": "Sanya,CN",
  "三沙": "Sansha,CN",
  "儋州": "Danzhou,CN",
  "五指山": "Wuzhishan,CN",
  "琼海": "Qionghai,CN",
  "文昌": "Wenchang,CN",
  "万宁": "Wanning,CN",
  "东方": "Dongfang,CN",
  
  # 四川省
  "成都": "Chengdu,CN",
  "自贡": "Zigong,CN",
  "攀枝花": "Panzhihua,CN",
  "泸州": "Luzhou,CN",
  "德阳": "Deyang,CN",
  "绵阳": "Mianyang,CN",
  "广元": "Guangyuan,CN",
  "遂宁": "Suining,CN",
  "内江": "Neijiang,CN",
  "乐山": "Leshan,CN",
  "南充": "Nanchong,CN",
  "眉山": "Meishan,CN",
  "宜宾": "Yibin,CN",
  "广安": "Guang'an,CN",
  "达州": "Dazhou,CN",
  "雅安": "Ya'an,CN",
  "巴中": "Bazhong,CN",
  "资阳": "Ziyang,CN",
  "阿坝藏族羌族自治州": "Aba,CN",
  "甘孜藏族自治州": "Garze,CN",
  "凉山彝族自治州": "Liangshan,CN",
  
  # 贵州省
  "贵阳": "Guiyang,CN",
  "六盘水": "Liupanshui,CN",
  "遵义": "Zunyi,CN",
  "安顺": "Anshun,CN",
  "毕节": "Bijie,CN",
  "铜仁": "Tongren,CN",
  "黔西南布依族苗族自治州": "Qianxinan,CN",
  "黔东南苗族侗族自治州": "Qiandongnan,CN",
  "黔南布依族苗族自治州": "Qiannan,CN",
  
  # 云南省
  "昆明": "Kunming,CN",
  "曲靖": "Qujing,CN",
  "玉溪": "Yuxi,CN",
  "保山": "Baoshan,CN",
  "昭通": "Zhaotong,CN",
  "丽江": "Lijiang,CN",
  "普洱": "Pu'er,CN",
  "临沧": "Lincang,CN",
  "楚雄彝族自治州": "Chuxiong,CN",
  "红河哈尼族彝族自治州": "Honghe,CN",
  "文山壮族苗族自治州": "Wenshan,CN",
  "西双版纳傣族自治州": "Xishuangbanna,CN",
  "大理白族自治州": "Dali,CN",
  "德宏傣族景颇族自治州": "Dehong,CN",
  "怒江傈僳族自治州": "Nujiang,CN",
  "迪庆藏族自治州": "Diqing,CN",
  
  # 西藏自治区
  "拉萨": "Lhasa,CN",
  "日喀则": "Shigatse,CN",
  "昌都": "Qamdo,CN",
  "林芝": "Nyingchi,CN",
  "山南": "Shannan,CN",
  "那曲": "Nagqu,CN",
  "阿里地区": "Ngari,CN",
  
  # 陕西省
  "西安": "Xi'an,CN",
  "铜川": "Tongchuan,CN",
  "宝鸡": "Baoji,CN",
  "咸阳": "Xianyang,CN",
  "渭南": "Weinan,CN",
  "延安": "Yan'an,CN",
  "汉中": "Hanzhong,CN",
  "榆林": "Yulin,CN",
  "安康": "Ankang,CN",
  "商洛": "Shangluo,CN",
  
  # 甘肃省
  "兰州": "Lanzhou,CN",
  "嘉峪关": "Jiayuguan,CN",
  "金昌": "Jinchang,CN",
  "白银": "Baiyin,CN",
  "天水": "Tianshui,CN",
  "武威": "Wuwei,CN",
  "张掖": "Zhangye,CN",
  "平凉": "Pingliang,CN",
  "酒泉": "Jiuquan,CN",
  "庆阳": "Qingyang,CN",
  "定西": "Dingxi,CN",
  "陇南": "Longnan,CN",
  "临夏回族自治州": "Linxia,CN",
  "甘南藏族自治州": "Gannan,CN",
  
  # 青海省
  "西宁": "Xining,CN",
  "海东": "Haidong,CN",
  "海北藏族自治州": "Haibei,CN",
  "黄南藏族自治州": "Huangnan,CN",
  "海南藏族自治州": "Hainan,CN",
  "果洛藏族自治州": "Golog,CN",
  "玉树藏族自治州": "Yushu,CN",
  "海西蒙古族藏族自治州": "Haixi,CN",
  
  # 宁夏回族自治区
  "银川": "Yinchuan,CN",
  "石嘴山": "Shizuishan,CN",
  "吴忠": "Wuzhong,CN",
  "固原": "Guyuan,CN",
  "中卫": "Zhongwei,CN",
  
  # 新疆维吾尔自治区
  "乌鲁木齐": "Urumqi,CN",
  "克拉玛依": "Karamay,CN",
  "吐鲁番": "Turpan,CN",
  "哈密": "Hami,CN",
  "昌吉回族自治州": "Changji,CN",
  "博尔塔拉蒙古自治州": "Bortala,CN",
  "巴音郭楞蒙古自治州": "Bayingolin,CN",
  "阿克苏地区": "Aksu,CN",
  "克孜勒苏柯尔克孜自治州": "Kizilsu,CN",
  "喀什地区": "Kashgar,CN",
  "和田地区": "Hotan,CN",
  "伊犁哈萨克自治州": "Ili,CN",
  "塔城地区": "Tacheng,CN",
  "阿勒泰地区": "Altay,CN",
  
  # 港澳台
  "香港": "Hong Kong,HK",
  "澳门": "Macau,MO",
  "台北": "Taipei,TW",
  "高雄": "Kaohsiung,TW",
  "台中": "Taichung,TW",
  "台南": "Tainan,TW",
  "基隆": "Keelung,TW",
  "新竹": "Hsinchu,TW",
  "嘉义": "Chiayi,TW"
}


def get_weather_by_city(city: str) -> Dict[str, Any]:
  """
  获取城市实时天气
  使用OpenWeatherMap API，失败时降级为mock数据
  
  Args:
    city: 城市名称（支持中文或英文）
    
  Returns:
    包含temperature(温度)、condition(天气状况)的字典
  """
  # 转换中文城市名为OpenWeather格式
  query_city = CITY_NAME_MAP.get(city, city)
  weather = _get_openweather(query_city)
  
  if weather:
    return weather
  
  # 降级：返回mock数据
  print(f"⚠️  天气API调用失败，返回默认天气: {city}")
  return {
    "temperature": 20,
    "condition": "Sunny"
  }


def _get_openweather(city: str) -> Optional[Dict[str, Any]]:
  """
  调用OpenWeatherMap API
  
  Args:
    city: 城市名（应为"City,CN"格式）
  """
  api_key = settings.OPENWEATHER_API_KEY
  if not api_key:
    print(f"⚠️  OpenWeather API KEY未配置")
    return None
  
  try:
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
      "q": city,
      "appid": api_key,
      "units": "metric",  # 摄氏度
      "lang": "zh_cn"
    }
    response = requests.get(url, params=params, timeout=5)
    data = response.json()
    
    if data.get("cod") != 200:
      print(f"❌ OpenWeather API返回错误: {data.get('cod')}, message={data.get('message')}, city={city}")
      return None
    
    temp = int(data["main"]["temp"])
    weather_main = data["weather"][0]["main"]
    weather_desc = data["weather"][0].get("description", "")
    
    # 映射到标准天气状态
    condition_map = {
      "Clear": "Sunny",
      "Clouds": "Cloudy",
      "Rain": "Rainy",
      "Snow": "Snowy",
      "Drizzle": "Light Rain",
      "Thunderstorm": "Rainy",
      "Mist": "Foggy",
      "Fog": "Foggy",
      "Haze": "Foggy"
    }
    condition = condition_map.get(weather_main, "Cloudy")
    
    print(f"✅ 获取到 {city} 实时天气: {temp}°C {weather_main}")
    return {
      "temperature": temp,
      "condition": condition
    }
    
  except Exception as e:
    print(f"❌ OpenWeather API调用异常: {e}")
    import traceback
    traceback.print_exc()
    return None