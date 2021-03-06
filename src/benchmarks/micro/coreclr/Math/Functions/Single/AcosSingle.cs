﻿// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.
// See the LICENSE file in the project root for more information.

using System;
using BenchmarkDotNet.Attributes;

namespace System.MathBenchmarks
{
    public partial class Single
    {
        // Tests MathF.Acos(float) over 5000 iterations for the domain -1, +1

        private const float acosDelta = 0.0004f;
        private const float acosExpectedResult = 7852.41084f;

        [Benchmark]
        public void Acos() => AcosTest();

        public static void AcosTest()
        {
            var result = 0.0f; var value = -1.0f;

            for (var iteration = 0; iteration < MathTests.Iterations; iteration++)
            {
                value += acosDelta;
                result += MathF.Acos(value);
            }

            var diff = MathF.Abs(acosExpectedResult - result);

            if (diff > MathTests.SingleEpsilon)
            {
                throw new Exception($"Expected Result {acosExpectedResult,10:g9}; Actual Result {result,10:g9}");
            }
        }
    }
}
