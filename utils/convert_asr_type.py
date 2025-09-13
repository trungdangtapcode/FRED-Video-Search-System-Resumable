
import unicodedata

BANG_XOA_DAU = str.maketrans(
    "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴáàảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ",
    "A"*17 + "D" + "E"*11 + "I"*5 + "O"*17 + "U"*11 + "Y"*5 + "a"*17 + "d" + "e"*11 + "i"*5 + "o"*17 + "u"*11 + "y"*5
)

def xoa_dau(txt: str) -> str:
    if not unicodedata.is_normalized("NFC", txt):
        txt = unicodedata.normalize("NFC", txt)
    return txt.translate(BANG_XOA_DAU)

MAX_LENGHT_PART = 40 # if longer split to multiple parts
OVERLAP_LENGTH = 20

def shorten_asr(asr_data_ori):
    asr_data = {}
    for video_id, lst_transript in asr_data_ori.items():
        tmp = [] # [{'start': int, 'duration': int, 'asr': str}]
        for segment in lst_transript: # check if segment duration > MAX_LENGHT_PART
            start, duration, asr = segment['start'], segment['duration'], segment['text']
            if len(asr)<=MAX_LENGHT_PART:
                tmp.append({
                    "start": start,
                    "duration": duration,
                    "text": xoa_dau(asr.lower())
                })
            else: # split
                words = asr.split()
                current_part = []
                current_start = start
                # print('words', len(words),words)
                for word in words:
                    if len(" ".join(current_part + [word])) <= MAX_LENGHT_PART:
                        current_part.append(word)
                    else:
                        # save current part, without overlap
                        # tmp.append({
                        # 	"start": current_start,
                        # 	"duration": len(current_part)*duration/len(words),
                        # 	"asr": xoa_dau(" ".join(current_part).lower())
                        # })
                        # # start new part
                        # current_start += len(current_part)*duration/len(words)
                        # current_part = [word]
                        
                        # save current part, with overlap
                        if current_part:
                            tmp.append({
                                "start": current_start,
                                "duration": len(current_part)*duration/len(words),
                                "text": xoa_dau(" ".join(current_part).lower())
                            })
                        # start new part with few overlapping words
                        num_words_prev_part = 0 # number of words to overlap from previous part, that fit in OVERLAP_LENGTH (THIS LENGTH IS CHARACTER LENGTH)
                        prev_part  = []
                        for w in reversed(current_part):
                            if len(" ".join(prev_part + [w])) <= OVERLAP_LENGTH:
                                prev_part = [w] + prev_part
                                num_words_prev_part += 1
                            else:
                                break
                        current_start += (len(current_part)-num_words_prev_part)*duration/len(words)
                        current_part = prev_part + [word]

                # save last part
                if current_part:
                    tmp.append({
                        "start": current_start,
                        "duration": len(current_part)*duration/len(words),
                        "text": xoa_dau(" ".join(current_part).lower())
                    })
        # 		print(segment)
        # 		print('tmp',tmp)
        # 		c += 1
        # 		break
        # if c>0:
        # 	break
        asr_data[video_id] = tmp


MIN_LENGHT = 150
MAX_LENGHT = 200

def convert_asr_type(frame_data, asr_data):
    asr_data = shorten_asr(asr_data)
    result = []
    from tqdm import tqdm
    for idx, frame in tqdm(list(enumerate(frame_data))[:]):
        video_id = frame["video_path"].split("/")[-1].split(".mp4")[0]
        if video_id in asr_data:
            transcript = asr_data[video_id]
            idx_asr = 0
            for i in range(len(transcript)-1):
                idx_asr = i
                if frame["timestamp"] >= transcript[i]["start"] and frame["timestamp"] <= transcript[i]["start"]+transcript[i]["duration"]:
                    break
            concat_text = ""

            # radius = 0
            # while True:
            # 	concat_text = ""
            # 	for j in range(max(0, idx_asr-radius), min(len(transcript), idx_asr+radius+1)):
            # 		concat_text += transcript[j]["text"] + " "
            # 	concat_text = xoa_dau(concat_text.strip())
            # 	if len(concat_text) > MAX_LENGHT:
            # 		radius -= 1
            # 		concat_text = ""
            # 		for j in range(max(0, idx_asr-radius), min(len(transcript), idx_asr+radius+1)):
            # 			concat_text += transcript[j]["text"] + " "
            # 		concat_text = xoa_dau(concat_text.strip())
            # 		break
            # 	if len(concat_text) >= MIN_LENGHT:
            # 		break
            # 	radius += 1
            # 	if radius > 10:
            # 		break
            
            


            # add token before and after the current caption (equal lenght)
    
            # interpolate_pos = len(transcript[idx_asr]["text"])/transcript[idx_asr]["duration"]*(frame["timestamp"]-transcript[idx_asr]["start"])
            # interpolate_pos = max(0, min(interpolate_pos, len(transcript[idx_asr]["text"])))
            # print(interpolate_pos, transcript[idx_asr]["duration"], len(transcript[idx_asr]["text"]), frame["timestamp"], transcript[idx_asr]["start"])
            
            # expand to left and right		
            # left_offset = int(interpolate_pos)
            # radius = 0
            # while True:
            # 	concat_text = ""
            # 	for j in range(max(0, idx_asr-radius), min(len(transcript), idx_asr+radius+1)):
            # 		concat_text += transcript[j]["text"] + " "
            # 	concat_text = xoa_dau(concat_text.strip())
            # 	if len(concat_text) > MAX_LENGHT:
            # 		radius -= 1
            # 		left_offset -= len(transcript[max(0, idx_asr-radius)]["text"]) + 1
            # 		concat_text = ""
            # 		for j in range(max(0, idx_asr-radius), min(len(transcript), idx_asr+radius+1)):
            # 			concat_text += transcript[j]["text"] + " "
            # 		concat_text = xoa_dau(concat_text.strip())
            # 		break
            # 	if len(concat_text) >= MIN_LENGHT:
            # 		break
            # 	radius += 1
            # 	if radius > 10:
            # 		break
            # break
    
            radius = 2
            for j in range(max(0, idx_asr-radius), min(len(transcript), idx_asr+radius+1)):
                concat_text += transcript[j]["text"] + " "
    
    
            concat_text = xoa_dau(concat_text.strip())
            tmp ={}
            tmp["idx"] = idx
            tmp["asr"] = concat_text
            
            result.append(tmp)
            # print(frame["timestamp"], concat_text)
        else:
            print(f"{video_id} not in asr_data")
            # raise ValueError(f"{video_id} not in asr_data")
            
if __name__ == "__main__":
    import json
    # path = "/data/root/data/frames_metadata_v2.json"
    # with open(path, "r") as f:
    #     frame_data = json.load(f)
    
    # path = "/data/root/yt_caption_full2.json"
    # with open(path, "r") as f:
    #     asr_data = json.load(f)
    
    # result = convert_asr_type(frame_data, asr_data)
    
    # with open("/data/root/data/frame_asr_v3.json", "w") as f:
    #     json.dump(result, f, ensure_ascii=False, indent=4)
    
    # print("Done!")