import itertools
import os
import music21
from music21 import pitch
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelChordGenerator:
    """多线程加速的和弦生成器"""

    def __init__(self):
        # 和弦模板配置
        self.major = [0, 4, 7]
        self.minor = [0, 3, 7]
        self.C4 = 48  # MIDI音符范围
        self.B4 = 59

        # 预生成所有可能的大三/小三和弦模板
        self.templates = (
                [[n + i for n in self.major] for i in range(self.C4, self.B4 + 1)] +
                [[n + i for n in self.minor] for i in range(self.C4, self.B4 + 1)]
        )

    def _get_chord_name(self, notes):
        """将音符列表转为和弦名称（如 C_major）"""
        root = min(notes)
        intervals = sorted(n - root for n in notes)
        chord_type = "major" if intervals == [0, 4, 7] else "minor"
        return f"{pitch.Pitch(root).name.replace('-', 'b')}_{chord_type}"

    def _save_single(self, progression, output_dir):
        """单个和弦进行的保存逻辑"""
        try:
            chord_names = [self._get_chord_name(chord) for chord in progression]
            filename = "-".join(chord_names) + ".mid"

            s = music21.stream.Stream()
            for chord_notes in progression:
                s.append(music21.chord.Chord(chord_notes))

            s.write('midi', fp=os.path.join(output_dir, filename))
            return True
        except:
            return False

    def generate_all(self, num_chords=4, output_dir="chord_output", max_workers=8):
        """全量生成所有组合（多线程加速）"""
        os.makedirs(output_dir, exist_ok=True)

        # 生成所有可能的组合迭代器
        all_combinations = itertools.product(self.templates, repeat=num_chords)
        total = (len(self.templates)) ** num_chords  # 总组合数

        # 进度条配置
        pbar = tqdm(total=total, desc="🚀 生成进度", unit="seq")

        # 多线程处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            batch_size = 1000  # 每1000个任务提交一次

            for i, combo in enumerate(all_combinations):
                if i >= total:  # 安全限制
                    break

                futures.append(executor.submit(
                    self._save_single,
                    list(combo),
                    output_dir
                ))

                # 批量提交后等待部分完成
                if len(futures) >= batch_size:
                    for future in as_completed(futures):
                        pbar.update(1)
                        futures.remove(future)

            # 处理剩余任务
            for future in as_completed(futures):
                pbar.update(1)

        pbar.close()
        print(f"\n🎉 全部完成！共生成 {total} 个MIDI文件到 {output_dir}")


if __name__ == "__main__":
    generator = ParallelChordGenerator()

    # 启动生成（4和弦组合，8线程）
    generator.generate_all(
        num_chords=4,
        output_dir="chord_progressions",
        max_workers=8  # 根据CPU核心数调整
    )