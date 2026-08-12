import React, { useState } from 'react';

interface Glass3DCardProps {
  children: React.ReactNode;
  className?: string;
}

export default function Glass3DCard({
  children,
  className = '',
}: Glass3DCardProps) {
  const [transform, setTransform] = useState(
    'perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1) translateZ(0)'
  );

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -7;
    const rotateY = ((x - centerX) / centerX) * 7;

    setTransform(
      `perspective(1000px)
       rotateX(${rotateX}deg)
       rotateY(${rotateY}deg)
       scale(1.045)
       translateZ(20px)`
    );
  };

  const handleMouseLeave = () => {
    setTransform(
      'perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1) translateZ(0)'
    );
  };

  return (
    <div
      className={`
        group
        relative
        h-full
        rounded-2xl
        cursor-pointer

        border
        border-white/10

        bg-white/[0.018]

        backdrop-blur-[3px]

        shadow-[0_8px_30px_rgba(0,0,0,0.08)]

        transition-all
        duration-300
        ease-out

        hover:border-white/20
        hover:shadow-[0_25px_60px_rgba(0,0,0,0.18)]

        ${className}
      `}
      style={{
        transform,
        transformStyle: 'preserve-3d',
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Glow behind card */}

      <div
        className="
          absolute
          -inset-[1px]
          rounded-2xl
          opacity-0
          group-hover:opacity-100
          transition-opacity
          duration-300
          pointer-events-none
          bg-gradient-to-r
          from-accent/10
          via-transparent
          to-accent/10
          blur-xl
        "
      />

      {/* Card content */}

      <div
        className="
          relative
          z-10
          h-full
        "
        style={{
          transform: 'translateZ(15px)',
          transformStyle: 'preserve-3d',
        }}
      >
        {children}
      </div>

      {/* Shine */}

      <div
        className="
          absolute
          inset-0
          rounded-2xl
          pointer-events-none
          opacity-0
          group-hover:opacity-100
          transition-opacity
          duration-300
          bg-gradient-to-br
          from-white/[0.08]
          via-transparent
          to-transparent
        "
      />
    </div>
  );
}