# -*- coding: utf-8 -*-
# @Time    : 2018/6/11 15:54
# @Author  : zhoujun
import os
import sys

project = 'DBNet.pytorch'  # 工作项目根目录
sys.path.append(os.getcwd().split(project)[0] + project)

import argparse
import time
import torch
from tqdm.auto import tqdm


class EVAL():
    def __init__(self, model_path, gpu_id=0):
        from models import get_model
        from data_loader import get_dataloader
        from post_processing import get_post_processing
        from utils import get_metric
        self.device = torch.device("cuda:%s" % gpu_id)
        if gpu_id is not None:
            torch.backends.cudnn.benchmark = True
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        config = checkpoint['config']
        config['arch']['args']['pretrained'] = False

        self.validate_loader = get_dataloader(config['dataset']['validate'], config['distributed'])

        self.model = get_model(config['arch'])
        self.model.load_state_dict(checkpoint['state_dict'])
        self.model.to(self.device)

        self.post_process = get_post_processing(config['post_processing'])
        self.metric_cls = get_metric(config['metric'])

    def _eval(self):
        self.model.eval()
        # torch.cuda.empty_cache()  # speed up evaluating after training finished
        raw_metrics = []
        total_frame = 0.0
        total_time = 0.0
        for i, batch in tqdm(enumerate(self.validate_loader), total=len(self.validate_loader), desc='test model'):
            with torch.no_grad():
                # 数据进行转换和丢到gpu
                for key, value in batch.items():
                    if value is not None:
                        if isinstance(value, torch.Tensor):
                            batch[key] = value.to(self.device)
                start = time.time()
                preds = self.model(batch['img'])
                boxes, scores = self.post_process(batch, preds)
                total_frame += batch['img'].size()[0]
                total_time += time.time() - start
                raw_metric = self.metric_cls.validate_measure(batch, (boxes, scores))
                raw_metrics.append(raw_metric)
        metrics = self.metric_cls.gather_measure(raw_metrics)
        print('FPS:{}', format(total_frame / total_time))
        return metrics['recall'].avg, metrics['precision'].avg, metrics['fmeasure'].avg


def init_args():
    parser = argparse.ArgumentParser(description='DBNet.pytorch')
    parser.add_argument('--model_path', required=True, type=str)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = init_args()
    eval = EVAL(args.model_path)
    result = eval.eval()
    print(result)