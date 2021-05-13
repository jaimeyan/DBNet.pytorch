import os

def main():
    data_path = './datasets'
    for _, _, files in os.walk('./train/img'):
        imgs = files

    for _, _, files in os.walk('./train/gt'):
        txts = files

    for type_ in ['train','test']:
        with open(type_ + '.txt', 'a') as f:
            for img in imgs:
                if 'gt_' + img.split('.')[0] + '.txt' in txts:
                    number = img.split('.')[0][4:]
                    f.write(os.path.join(data_path, type_, 'img', number + '.jpg'))
                    f.write('\t')
                    f.write(os.path.join(data_path, type_, 'gt', number + '.txt'))
                    f.write('\n')

if __name__ == '__main__':
    main()