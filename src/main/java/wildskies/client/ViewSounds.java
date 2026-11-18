package wildskies.client;

import java.util.concurrent.CompletableFuture;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.Sound;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.client.sounds.AudioStream;
import net.minecraft.client.sounds.SoundBufferLibrary;
import net.minecraft.client.sounds.SoundManager;
import net.minecraft.client.sounds.WeighedSoundEvents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

/** The star view's sound: its own quiet loops, and the rest of the world turned down while you look. */
public final class ViewSounds {
    private ViewSounds() {
    }

    /** A loop that follows the view's opening and stops when it closes. */
    public static final class Loop extends AbstractTickableSoundInstance {
        private final float base;

        public Loop(SoundEvent sound, float volume, float pitch) {
            super(sound, SoundSource.AMBIENT, SoundInstance.createUnseededRandom());
            this.base = volume;
            this.looping = true;
            this.delay = 0;
            this.relative = true;
            this.attenuation = Attenuation.NONE;
            this.volume = 0.001f;
            this.pitch = pitch;
        }

        @Override
        public void tick() {
            if (!StarView.active()) {
                stop();
                return;
            }
            volume = Math.max(0.001f, base * StarView.openAmount(1f));
        }

        @Override
        public boolean canStartSilent() {
            return true;
        }
    }

    /** Wraps another (non-ticking) sound and turns it down. */
    public static final class Muffled implements SoundInstance {
        private final SoundInstance in;
        private final float k;

        public Muffled(SoundInstance in, float k) {
            this.in = in;
            this.k = k;
        }

        @Override
        public ResourceLocation getLocation() {
            return in.getLocation();
        }

        @Override
        public WeighedSoundEvents resolve(SoundManager manager) {
            return in.resolve(manager);
        }

        @Override
        public Sound getSound() {
            return in.getSound();
        }

        @Override
        public SoundSource getSource() {
            return in.getSource();
        }

        @Override
        public boolean isLooping() {
            return in.isLooping();
        }

        @Override
        public boolean isRelative() {
            return in.isRelative();
        }

        @Override
        public int getDelay() {
            return in.getDelay();
        }

        @Override
        public float getVolume() {
            return in.getVolume() * k;
        }

        @Override
        public float getPitch() {
            return in.getPitch();
        }

        @Override
        public double getX() {
            return in.getX();
        }

        @Override
        public double getY() {
            return in.getY();
        }

        @Override
        public double getZ() {
            return in.getZ();
        }

        @Override
        public Attenuation getAttenuation() {
            return in.getAttenuation();
        }

        @Override
        public boolean canStartSilent() {
            return in.canStartSilent();
        }

        @Override
        public boolean canPlaySound() {
            return in.canPlaySound();
        }

        @Override
        public CompletableFuture<AudioStream> getStream(SoundBufferLibrary lib, Sound sound, boolean looping) {
            return in.getStream(lib, sound, looping);
        }
    }
}
