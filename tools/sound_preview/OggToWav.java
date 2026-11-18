import org.lwjgl.stb.STBVorbis;
import org.lwjgl.system.MemoryStack;
import java.io.*;
import java.nio.*;
import java.nio.file.*;

/** Decodes vanilla .ogg files to 16-bit WAV (mono mix) with LWJGL's stb_vorbis: java OggToWav in.ogg out.wav ... */
public class OggToWav {
    public static void main(String[] a) throws Exception {
        for (int i = 0; i + 1 < a.length; i += 2) {
            byte[] raw = Files.readAllBytes(Path.of(a[i]));
            ByteBuffer in = ByteBuffer.allocateDirect(raw.length).put(raw).flip();
            try (MemoryStack st = MemoryStack.stackPush()) {
                IntBuffer ch = st.mallocInt(1), rate = st.mallocInt(1);
                ShortBuffer pcm = STBVorbis.stb_vorbis_decode_memory(in, ch, rate);
                int c = ch.get(0), r = rate.get(0), n = pcm.remaining() / c;
                ByteArrayOutputStream b = new ByteArrayOutputStream();
                DataOutputStream d = new DataOutputStream(b);
                for (int s = 0; s < n; s++) {
                    int v = 0;
                    for (int k = 0; k < c; k++) v += pcm.get(s * c + k);
                    v /= c;
                    d.writeByte(v & 255); d.writeByte((v >> 8) & 255);
                }
                byte[] data = b.toByteArray();
                ByteBuffer h = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
                h.put("RIFF".getBytes()).putInt(36 + data.length).put("WAVEfmt ".getBytes()).putInt(16).putShort((short) 1)
                        .putShort((short) 1).putInt(r).putInt(r * 2).putShort((short) 2).putShort((short) 16)
                        .put("data".getBytes()).putInt(data.length);
                try (OutputStream o = new FileOutputStream(a[i + 1])) { o.write(h.array()); o.write(data); }
            }
        }
    }
}
